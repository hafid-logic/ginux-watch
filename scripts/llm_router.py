#!/usr/bin/env python3
"""llm_router.py — ordered multi-provider LLM router (directive v6.3 item 6).

Policy:
  - per request: timeout 120s (config request_timeout_s), 2 attempts with
    linear backoff (config attempts_per_model / backoff_s).
  - 401/403 -> error class auth_failed, NO retry, skip to next PROVIDER.
  - 429 / 5xx / timeout / network / bad JSON -> retryable; attempts exhausted
    -> next MODEL, then next PROVIDER.
  - state/llm-status.json: per provider {configured, status, model_current,
    last_success, last_error_class, consecutive_failures, rate_limit}.
  - 3 consecutive provider-level failures -> status "down" and an
    outbox/ALERT-llm-<provider>.md file is written (error classes only, no
    secrets, idempotent overwrite).
  - the workflow fails ONLY if every CONFIGURED provider fell; with zero
    configured providers the router reports "awaiting secrets" and exits 2
    (soft) — absence of keys is a config state, not an outage.
  - secret scan on the outgoing payload BEFORE send: any hit aborts (exit 3),
    nothing is transmitted.

CLI:
  python3 scripts/llm_router.py --system-file S --user-file U \
      [--config config/llm-providers.yml] [--state state/llm-status.json]
      [--out-text P]
Exit: 0 = answered; 1 = all configured providers failed; 2 = none configured;
      3 = secret in payload (nothing sent)."""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config/llm-providers.yml"
DEFAULT_STATE = ROOT / "state/llm-status.json"
ALERTS_DIR = ROOT / "outbox"

SECRET_PATTERNS = [
    ("ghp_", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("gho_", re.compile(r"gho_[A-Za-z0-9]{20,}")),
    ("github_pat_", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("AKIA", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("xox", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("glpat-", re.compile(r"glpat-[A-Za-z0-9_-]{15,}")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

RETRYABLE_HTTP = {429, 500, 502, 503, 504, 529}


class SecretInPayload(Exception):
    pass


class AllProvidersFailed(Exception):
    pass


def scan_secrets(text):
    return [name for name, pat in SECRET_PATTERNS if pat.search(text or "")]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path):
    import yaml
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


class Status:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {"updated": None, "providers": {}, "last_call": None}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        if not isinstance(self.data.get("providers"), dict):
            self.data["providers"] = {}

    def ensure(self, name):
        return self.data["providers"].setdefault(name, {
            "configured": False, "status": "unconfigured", "model_current": None,
            "last_success": None, "last_error_class": None,
            "consecutive_failures": 0, "rate_limit": None,
        })

    def save(self):
        self.data["updated"] = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")


def write_alert(provider, st, error_class):
    """outbox/ALERT-llm-<provider>.md — no secrets, error classes only."""
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    p = ALERTS_DIR / ("ALERT-llm-%s.md" % provider)
    body = (
        "# ALERT: LLM provider %s — %s\n\n"
        "- time: %s\n- status: %s\n- error_class: %s\n"
        "- consecutive_failures: %s\n"
        "- action: no automatic retry storm; the next session report opens "
        "with the providers status line and names the missing/failed secret\n"
        % (st.get("status", "down"), provider, now_iso(),
           st.get("status", "down"), error_class,
           st.get("consecutive_failures", 0))
    )
    p.write_text(body, encoding="utf-8")


def http_json(url, payload, api_key, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key,
            "User-Agent": "ginux-watch-llm-router/1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8")), dict(r.headers)


def extract_rate_limit(headers):
    out = {}
    for k, v in (headers or {}).items():
        lk = k.lower()
        if lk.startswith("x-ratelimit") or lk.startswith("ratelimit"):
            out[lk] = str(v)
    return out or None


def call_chat(cfg, state, system, user, meta_out):
    """Try providers/models in order. Returns response text; fills meta_out.
    Raises AllProvidersFailed (detail in .detail) when nothing configured or
    every configured provider failed."""
    providers = cfg.get("providers", [])
    timeout = int(cfg.get("request_timeout_s", 120))
    attempts = int(cfg.get("attempts_per_model", 2))
    backoff = float(cfg.get("backoff_s", 5))
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))

    configured = 0
    last_errors = []
    for prov in providers:
        name = prov["name"]
        key = os.environ.get(prov.get("env_secret", ""), "").strip()
        st = state.ensure(name)
        st["configured"] = bool(key)
        state.save()
        if not key:
            st["status"] = "unconfigured"
            state.save()
            continue
        configured += 1
        if st.get("status") == "auth_failed":
            last_errors.append("%s:auth_failed(persist)" % name)
            continue
        base = prov["base_url"].rstrip("/")
        auth_broken = False
        for model in prov.get("models", []):
            if model.get("status") not in (None, "available"):
                continue
            err_class = None
            payload = {
                "model": model["id"],
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": 0.2,
                "stream": False,
            }
            for attempt in range(1, attempts + 1):
                t0 = time.monotonic()
                code, headers, resp, err_body = None, {}, None, ""
                try:
                    code, resp, headers = http_json(
                        base + "/chat/completions", payload, key, timeout)
                except urllib.error.HTTPError as e:
                    code = e.code
                    headers = dict(e.headers or {})
                    try:
                        err_body = e.read().decode("utf-8")[:200]
                    except Exception:
                        err_body = ""
                    if code in (401, 403):
                        st["status"] = "auth_failed"
                        st["last_error_class"] = "auth_failed"
                        st["model_current"] = model["id"]
                        state.data["last_call"] = {
                            "provider": name, "model": model["id"],
                            "outcome": "auth_failed", "at": now_iso()}
                        state.save()
                        write_alert(name, st, "auth_failed")
                        last_errors.append("%s:auth_failed" % name)
                        auth_broken = True
                        break  # no retry on auth errors
                    retryable = code in RETRYABLE_HTTP
                    err_class = "http_%d" % code
                except Exception as e:  # timeout / network / JSON decode
                    retryable = True
                    err_class = type(e).__name__.lower()
                    err_body = str(e)[:200]
                else:
                    retryable = False
                latency = round(time.monotonic() - t0, 2)
                text = None
                if not retryable:
                    try:
                        text = resp["choices"][0]["message"]["content"]
                    except Exception:
                        retryable = True
                        err_class = "bad_response_shape"
                        err_body = json.dumps(resp)[:200]
                if text is not None:
                    st.update({
                        "status": "ok", "model_current": model["id"],
                        "last_success": now_iso(), "last_error_class": None,
                        "consecutive_failures": 0,
                        "rate_limit": extract_rate_limit(headers),
                    })
                    state.data["last_call"] = {
                        "provider": name, "model": model["id"],
                        "latency_s": latency, "outcome": "ok", "at": now_iso(),
                    }
                    state.save()
                    meta_out.update(provider=name, model=model["id"],
                                    latency_s=latency, attempts=attempt)
                    return text
                if attempt < attempts:
                    time.sleep(backoff)
            if auth_broken:
                break  # skip remaining models of this provider
            # attempts exhausted for this model -> count a provider-level failure
            st["model_current"] = model["id"]
            st["last_error_class"] = err_class
            cf = int(st.get("consecutive_failures", 0)) + 1
            st["consecutive_failures"] = cf
            if cf >= down_threshold:
                st["status"] = "down"
                write_alert(name, st, err_class)
            else:
                st["status"] = "degraded"
            state.data["last_call"] = {
                "provider": name, "model": model["id"],
                "outcome": err_class, "at": now_iso()}
            state.save()
            last_errors.append("%s:%s:%s" % (name, model["id"], err_class))
    detail = "none-configured" if configured == 0 else "all-failed:" + ";".join(last_errors[-8:])
    e = AllProvidersFailed(detail)
    e.detail = detail
    raise e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system-file", required=True)
    ap.add_argument("--user-file", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--state", default=str(DEFAULT_STATE))
    ap.add_argument("--out-text", default=None)
    args = ap.parse_args()

    system = Path(args.system_file).read_text(encoding="utf-8")
    user = Path(args.user_file).read_text(encoding="utf-8")

    hits = scan_secrets(system + "\n" + user)
    if hits:
        sys.stderr.write("secret scan HIT on payload: %s — NOTHING SENT\n" % ",".join(hits))
        return 3

    cfg = load_config(args.config)
    state = Status(args.state)
    meta = {}
    try:
        text = call_chat(cfg, state, system, user, meta)
    except AllProvidersFailed as e:
        state.save()
        if e.detail == "none-configured":
            print("PROVIDERS: none configured — awaiting secrets (%s)" %
                  ",".join(p.get("env_secret", "?") for p in cfg.get("providers", [])))
            return 2
        sys.stderr.write("PROVIDERS: %s\n" % e.detail)
        return 1
    state.save()
    if args.out_text:
        Path(args.out_text).write_text(text, encoding="utf-8")
    print("PROVIDERS: ok via %s/%s (%ss)" % (meta.get("provider"), meta.get("model"), meta.get("latency_s")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

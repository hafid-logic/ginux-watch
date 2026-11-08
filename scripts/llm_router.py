#!/usr/bin/env python3
"""llm_router.py — ordered multi-provider LLM router (directive v6.3 item 6,
extended by directive v6.4 item 4: daily per-provider call caps, rate-limit
observation on every response, directed per-model calls for eval, idempotent
ALERT files).

Policy:
  - per request: timeout 120s (config request_timeout_s), 2 attempts with
    linear backoff (config attempts_per_model / backoff_s).
  - 401/403 -> error class auth_failed, NO retry, skip to next PROVIDER.
  - 429 / 5xx / timeout / network / bad JSON -> retryable; attempts exhausted
    -> next MODEL, then next PROVIDER.
  - daily_call_cap_per_provider (v6.4): hard per-provider daily budget counted
    per HTTP attempt; cap_reached is NOT a failure (no ALERT, no
    consecutive_failures increment); remaining providers still serve.
  - state/llm-status.json: per provider {configured, status, model_current,
    last_success, last_error_class, consecutive_failures, rate_limit,
    retry_after_s} plus {"daily": {date_utc, calls per provider}}.
  - rate-limit headers (x-ratelimit-*, Retry-After) recorded on success AND
    on 429/5xx errors (v6.4 item 4 "record observed rate limits").
  - 3 consecutive provider-level failures -> status "down" and an
    outbox/ALERT-llm-<provider>.md file is written (error classes only, no
    secrets, idempotent — unchanged state never rewrites the file so the
    outbox/ push trigger cannot loop).
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
    ("nvapi_", re.compile(r"nvapi-[A-Za-z0-9_-]{20,}")),
    ("sk_", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{15,}\b")),
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
        self.data = {"updated": None, "providers": {}, "last_call": None,
                     "daily": {"date_utc": None, "calls": {}}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        if not isinstance(self.data.get("providers"), dict):
            self.data["providers"] = {}
        self.daily_ensure()

    def daily_ensure(self):
        """Per-provider daily call accounting (v6.4 item 4); resets at UTC date."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        d = self.data.get("daily")
        if not isinstance(d, dict) or d.get("date_utc") != today:
            d = {"date_utc": today, "calls": {}}
            self.data["daily"] = d
        if not isinstance(d.get("calls"), dict):
            d["calls"] = {}
        return d

    def daily_count(self, provider):
        return int(self.daily_ensure()["calls"].get(provider, 0))

    def daily_add(self, provider, n=1):
        d = self.daily_ensure()
        d["calls"][provider] = int(d["calls"].get(provider, 0)) + n
        return d["calls"][provider]

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
    """outbox/ALERT-llm-<provider>.md — no secrets, error classes only.
    Idempotent (v6.4 item 4): an unchanged (status, error_class) pair never
    rewrites the file, so timestamp churn cannot retrigger the outbox path."""
    p = ALERTS_DIR / ("ALERT-llm-%s.md" % provider)
    alert_key = "%s:%s" % (st.get("status", "down"), error_class)
    if st.get("last_alert_key") == alert_key and p.exists():
        return
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    body = (
        "# ALERT: LLM provider %s — %s\n\n"
        "- time: %s\n- status: %s\n- error_class: %s\n"
        "- consecutive_failures: %s\n"
        "- retry_after_s: %s\n"
        "- action: no automatic retry storm; the next session report opens "
        "with the providers status line and names the missing/failed secret\n"
        % (st.get("status", "down"), provider, now_iso(),
           st.get("status", "down"), error_class,
           st.get("consecutive_failures", 0),
           st.get("retry_after_s", "n/a"))
    )
    p.write_text(body, encoding="utf-8")
    st["last_alert_key"] = alert_key


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


def capture_rate_limit(st, headers):
    """Record observed rate-limit headers on success AND error paths (v6.4)."""
    rl = extract_rate_limit(headers)
    if rl:
        st["rate_limit"] = rl
    ra = (headers or {}).get("Retry-After") or (headers or {}).get("retry-after")
    if ra:
        st["retry_after_s"] = str(ra)
    return rl


def call_chat(cfg, state, system, user, meta_out):
    """Try providers/models in order. Returns response text; fills meta_out.
    Raises AllProvidersFailed (detail in .detail) when nothing configured or
    every configured provider failed."""
    providers = cfg.get("providers", [])
    timeout = int(cfg.get("request_timeout_s", 120))
    attempts = int(cfg.get("attempts_per_model", 2))
    backoff = float(cfg.get("backoff_s", 5))
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))
    # v6.4 item 4: hard daily budget per provider, counted per HTTP attempt.
    # 0 = unlimited. cap_reached is NOT a provider failure: no ALERT, no
    # consecutive_failures increment; remaining providers still serve.
    daily_cap = int(cfg.get("daily_call_cap_per_provider", 60) or 0)

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
            cap_hit = False
            err_class = None
            payload = {
                "model": model["id"],
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": 0.2,
                "stream": False,
            }
            for attempt in range(1, attempts + 1):
                if daily_cap and state.daily_count(name) >= daily_cap:
                    cap_hit = True
                    err_class = "cap_reached"
                    break
                state.daily_add(name)
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
                    capture_rate_limit(st, headers)
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
            if cap_hit:
                st["last_error_class"] = "cap_reached"
                state.data["last_call"] = {
                    "provider": name, "outcome": "cap_reached", "at": now_iso()}
                state.save()
                last_errors.append("%s:cap_reached" % name)
                break  # provider is capped for today; stop burning models
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


def _fail(detail):
    e = AllProvidersFailed(detail)
    e.detail = detail
    return e


def call_model(cfg, state, provider_name, model_id, system, user, meta_out):
    """Directed call to ONE (provider, model) — eval path (v6.4 items 4/6).
    Same timeout/attempt/backoff policy and daily-cap accounting as call_chat;
    rate-limit headers captured on success AND on HTTP errors; auth_failed
    persists in status. Raises AllProvidersFailed with .detail = error class;
    never falls back to another provider (eval needs per-model rows)."""
    prov = None
    for p in cfg.get("providers", []):
        if p.get("name") == provider_name:
            prov = p
            break
    if prov is None:
        raise _fail("unknown-provider:%s" % provider_name)
    key = os.environ.get(prov.get("env_secret", ""), "").strip()
    if not key:
        raise _fail("unconfigured:%s" % provider_name)
    st = state.ensure(provider_name)
    st["configured"] = True
    state.save()
    daily_cap = int(cfg.get("daily_call_cap_per_provider", 60) or 0)
    if daily_cap and state.daily_count(provider_name) >= daily_cap:
        st["last_error_class"] = "cap_reached"
        state.save()
        raise _fail("cap_reached:%s" % provider_name)
    timeout = int(cfg.get("request_timeout_s", 120))
    attempts = int(cfg.get("attempts_per_model", 2))
    backoff = float(cfg.get("backoff_s", 5))
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))
    base = prov["base_url"].rstrip("/")
    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.2,
        "stream": False,
    }
    err_class = None
    for attempt in range(1, attempts + 1):
        if daily_cap and state.daily_count(provider_name) >= daily_cap:
            err_class = "cap_reached"
            break
        state.daily_add(provider_name)
        t0 = time.monotonic()
        code, headers, resp, text = None, {}, None, None
        retryable = True
        try:
            code, resp, headers = http_json(
                base + "/chat/completions", payload, key, timeout)
        except urllib.error.HTTPError as e:
            code = e.code
            headers = dict(e.headers or {})
            capture_rate_limit(st, headers)
            if code in (401, 403):
                st["status"] = "auth_failed"
                st["last_error_class"] = "auth_failed"
                st["model_current"] = model_id
                state.data["last_call"] = {
                    "provider": provider_name, "model": model_id,
                    "outcome": "auth_failed", "at": now_iso()}
                state.save()
                write_alert(provider_name, st, "auth_failed")
                raise _fail("auth_failed:%s" % provider_name)
            retryable = code in RETRYABLE_HTTP
            err_class = "http_%d" % code
        except Exception as e:
            retryable = True
            err_class = type(e).__name__.lower()
        else:
            retryable = False
        if not retryable:
            try:
                text = resp["choices"][0]["message"]["content"]
            except Exception:
                retryable = True
                err_class = "bad_response_shape"
        if text is not None:
            latency = round(time.monotonic() - t0, 2)
            st.update({
                "status": "ok", "model_current": model_id,
                "last_success": now_iso(), "last_error_class": None,
                "consecutive_failures": 0,
                "rate_limit": extract_rate_limit(headers),
            })
            state.data["last_call"] = {
                "provider": provider_name, "model": model_id,
                "latency_s": latency, "outcome": "ok", "at": now_iso()}
            state.save()
            meta_out.update(provider=provider_name, model=model_id,
                            latency_s=latency, attempts=attempt)
            return text
        if attempt < attempts:
            time.sleep(backoff)
    cf = int(st.get("consecutive_failures", 0)) + 1
    st["consecutive_failures"] = cf
    st["model_current"] = model_id
    st["last_error_class"] = err_class
    if cf >= down_threshold:
        st["status"] = "down"
        write_alert(provider_name, st, err_class)
    else:
        st["status"] = "degraded"
    state.data["last_call"] = {
        "provider": provider_name, "model": model_id,
        "outcome": err_class, "at": now_iso()}
    state.save()
    raise _fail("%s:%s:%s" % (provider_name, model_id, err_class))


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

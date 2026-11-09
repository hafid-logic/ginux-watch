#!/usr/bin/env python3
"""llm_router.py — ordered multi-provider LLM router (directive v6.3 item 6;
v6.4 item 4: daily caps, rate-limit capture, directed eval calls, idempotent
ALERTs; appendix v6.6 items 8-11/13 (2026-11-08): mandated provider order and
per-provider timeouts, failure taxonomy, no-secret diagnostics, tolerant JSON
extraction, probe gating + 30-minute circuit breaker, byte-level payload scan,
actual-model logging, total-failure ALERT).

Policy:
  - per request: timeout from per-provider request_timeout_s (falls back to
    global config request_timeout_s), 2 attempts with linear backoff.
  - failure taxonomy (appendix item 9): auth_failed (401/403, no retry),
    rate_limited (429), timeout, no_json (body not JSON), api_shape (HTTP 200
    but content missing/mis-shaped), schema_invalid (parsed reply failed the
    jsonschema gate, assigned by callers), http_5xx, http_<code>, urlerror,
    cap_reached.
  - auth_failed = needs_secret: skipped WITHOUT retry; the ALERT names the
    missing secret (appendix item 8).
  - answer field: ONLY choices[0].message.content is the answer. Any reply
    content found in other fields (reasoning, tool_calls, ...) is LOGGED by
    name in the diagnostics and never assumed (appendix item 10).
  - model_actual: the provider-resolved model from the response "model" field
    is recorded per call (matters for the openrouter/free alias, item 8).
  - diagnostics on every failure (appendix item 9) -> state/llm-status.json
    provider["last_diag"]: {http_status, resp_top_keys, finish_reason,
    content_len, noncontent_fields, usage, elapsed_s, excerpt200} — names and
    lengths only; the excerpt200 goes through the secret scan first.
  - circuit breaker (appendix item 11): a provider reaching the down threshold
    is skipped for circuit_breaker_skip_s (default 1800 s) via skip_until;
    call_chat honors it. Directed eval calls (call_model) intentionally do NOT
    honor it (eval measures every provider independently, item 12).
  - probe gating (appendix item 11): call_chat skips (provider, model) pairs
    whose latest entry in state/llm-probe.json has ok=false. Missing/stale
    probe file => no gating.
  - daily_call_cap_per_provider: hard per-provider daily budget counted per
    HTTP attempt; cap_reached is NOT a failure (no ALERT, no
    consecutive_failures increment); remaining providers still serve.
  - state/llm-status.json: per provider {configured, status, model_current,
    model_actual, last_success, last_error_class, last_diag,
    consecutive_failures, rate_limit, retry_after_s, skip_until, skip_until_iso}
    plus {"daily": {date_utc, calls per provider}}.
  - 3 consecutive provider-level failures -> status "down", skip_until set,
    and outbox/ALERT-llm-<provider>.md; when EVERY configured provider falls,
    an additional idempotent outbox/ALERT-llm-all-providers.md is written
    (appendix item 8: never hide a total failure). Error classes only — no
    secrets; unchanged state never rewrites an ALERT (no outbox push loop).
  - the workflow fails ONLY if every CONFIGURED provider fell; with zero
    configured providers the router reports "awaiting secrets" and exits 2
    (soft) — absence of keys is a config state, not an outage.
  - BYTE-LEVEL secret scan on the outgoing payload BEFORE send (appendix item
    13): any hit aborts (exit 3 / SecretInPayload), nothing is transmitted.

CLI:
  python3 scripts/llm_router.py --system-file S --user-file U \
      [--config config/llm-providers.yml] [--state state/llm-status.json]
      [--out-text P]
Exit: 0 = answered; 1 = all configured providers failed; 2 = none configured;
      3 = secret in payload (nothing sent)."""
import argparse
import json
import os
import random
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
DEFAULT_PROBE_STATE = ROOT / "state/llm-probe.json"
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

# byte-level twins of the same patterns (appendix item 13: payload is scanned
# as UTF-8 bytes right before the socket write)
BYTE_PATTERNS = [
    (name, re.compile(pat.pattern.encode("utf-8")))
    for name, pat in SECRET_PATTERNS
]

RETRYABLE_HTTP = {429, 500, 502, 503, 504, 529}  # 402 (needs_credit) and 401/403 never retry (v6.8-5)


class SecretInPayload(Exception):
    pass


class AllProvidersFailed(Exception):
    pass


def scan_secrets(text):
    return [name for name, pat in SECRET_PATTERNS if pat.search(text or "")]


def scan_secrets_bytes(data):
    """Byte-level scan (appendix item 13). data: bytes."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return [name for name, pat in BYTE_PATTERNS if pat.search(data)]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_config(path):
    import yaml
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# failure taxonomy (appendix item 9)
# ---------------------------------------------------------------------------

def classify_http(code):
    if code in (401, 403):
        return "auth_failed"
    if code == 402:
        # v6.8 item 5: payment required (e.g. OpenRouter credits) — terminal,
        # needs_credit, never retried ([MEASURED] 2026-11-08: kimi-k3.1-pro /
        # mistral-large-4-0 402 "requires more credits, or fewer max_tokens")
        return "needs_credit"
    if code == 429:
        return "rate_limited"
    if 500 <= code <= 599:
        return "http_5xx"
    return "http_%d" % code


def classify_exc(e):
    name = type(e).__name__.lower()
    if "timeout" in name or "timedout" in name:
        return "timeout"
    if isinstance(e, json.JSONDecodeError) or "jsondecode" in name:
        return "no_json"
    if isinstance(e, urllib.error.URLError) and "timed out" in str(e.reason).lower():
        return "timeout"
    return name or "error"


def extract_json_object(text):
    """Tolerant JSON extraction (appendix item 10):
    1. strip ``` fences anywhere in the text;
    2. if text precedes the JSON, take the FIRST balanced {...} block;
    3. return the parsed object — caller applies jsonschema.
    Raises ValueError("no_json") when no balanced object exists."""
    t = text or ""
    t = t.replace("```json", "```").replace("```JSON", "```")
    if "```" in t:
        parts = t.split("```")
        # prefer a fenced part that contains an object
        for part in parts:
            if "{" in part:
                t = part
                break
    start = t.find("{")
    if start == -1:
        raise ValueError("no_json: no '{' in reply")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                block = t[start:i + 1]
                try:
                    return json.loads(block)
                except json.JSONDecodeError as e:
                    raise ValueError("no_json: unparseable block (%s)" % str(e)[:80])
    raise ValueError("no_json: unbalanced object")


def diag_from_failure(resp, code, headers, raw_body, elapsed_s, err_class):
    """Appendix item 9 — no-secret diagnostic block for one failed attempt."""
    diag = {
        "error_class": err_class,
        "http_status": code,
        "resp_top_keys": sorted(resp.keys()) if isinstance(resp, dict) else None,
        "finish_reason": None,
        "content_len": None,
        "noncontent_fields": None,
        "usage": resp.get("usage") if isinstance(resp, dict) else None,
        "elapsed_s": elapsed_s,
    }
    try:
        msg = resp["choices"][0]["message"]
        diag["finish_reason"] = resp["choices"][0].get("finish_reason")
        content = msg.get("content")
        diag["content_len"] = len(content) if isinstance(content, str) else None
        extra = sorted(k for k in msg.keys()
                       if k != "content" and msg.get(k) not in (None, "", [], {}))
        diag["noncontent_fields"] = extra or None
    except Exception:
        pass
    excerpt = ""
    if raw_body:
        excerpt = raw_body[:200]
    elif isinstance(resp, dict):
        excerpt = json.dumps(resp)[:200]
    hits = scan_secrets(excerpt)
    if hits:
        excerpt = "[redacted:secret-shaped:%s]" % ",".join(hits)
    diag["excerpt200"] = excerpt
    return diag


def answer_and_shape(resp):
    """Returns (content, noncontent_fields, model_actual). content is None when
    the reply shape carries no usable content field; noncontent_fields lists
    (names only) any other populated message fields — logged, never used as
    the answer (appendix item 10)."""
    model_actual = resp.get("model") if isinstance(resp, dict) else None
    noncontent = []
    try:
        msg = resp["choices"][0]["message"]
        content = msg.get("content")
        noncontent = sorted(k for k in msg.keys()
                            if k != "content" and msg.get(k) not in (None, "", [], {}))
        if isinstance(content, str) and content.strip():
            return content, (noncontent or None), model_actual
    except Exception:
        content = None
    return None, (noncontent or None), model_actual


def shape_failure_class(resp, max_tokens):
    """v6.9-6 / v7.0-4b: classify an HTTP-200 reply whose content is missing or
    blank. Returns (err_class, finish_reason, usage). reasoning_exhausted when
    finish_reason=length AND reasoning_tokens >= 0.8*max_tokens — the output
    budget was consumed by reasoning before any content was emitted; NOT
    retryable (v6.9-6: classified reasoning_exhausted, not api_shape, no
    retry). Any other missing/blank shape stays api_shape (retryable)."""
    finish_reason = None
    usage = resp.get("usage") if isinstance(resp, dict) else None
    try:
        finish_reason = resp["choices"][0].get("finish_reason")
    except Exception:
        finish_reason = None
    rt = 0
    try:
        rt = int(((usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
    except Exception:
        rt = 0
    if finish_reason == "length" and max_tokens and rt >= int(0.8 * max_tokens):
        return "reasoning_exhausted", finish_reason, usage
    return "api_shape", finish_reason, usage


def success_shape_meta(resp):
    """v7.0-4b: names/numbers only from a SUCCESS reply — finish_reason plus a
    small usage summary; never the content itself."""
    fr = None
    try:
        fr = resp["choices"][0].get("finish_reason")
    except Exception:
        fr = None
    usage = None
    try:
        u = resp.get("usage") or {}
        usage = {"completion_tokens": u.get("completion_tokens"),
                 "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}
    except Exception:
        usage = None
    return fr, usage


def throttle_provider(prov, st):
    """v6.9-2: per-provider minimum send interval — config min_interval_s wins,
    else 60/rpm seconds (rpm<=0 or absent means NO throttle). Sleeps in-place
    when called too soon; persists _last_send_epoch (wall clock) in state.
    Returns the waited seconds."""
    iv = prov.get("min_interval_s")
    if iv is None:
        rpm = prov.get("rpm") or 0
        iv = (60.0 / rpm) if rpm and rpm > 0 else 0
    try:
        iv = float(iv)
    except Exception:
        iv = 0.0
    if iv <= 0:
        return 0.0
    now = time.time()
    try:
        last = float(st.get("_last_send_epoch") or 0)
    except Exception:
        last = 0.0
    wait = last + iv - now
    if wait > 0:
        time.sleep(wait)
    st["_last_send_epoch"] = time.time()
    return max(0.0, wait)


def rate_limit_429_plan(st, headers, backoff_s):
    """v6.9-2: on a 429 — respect Retry-After capped at 120s plus jitter;
    a SECOND consecutive 429 flips the provider status to rate_limited and
    stops burning quota (caller breaks out of the provider). Returns
    (wait_s, stop_provider)."""
    c429 = int(st.get("consecutive_429") or 0) + 1
    st["consecutive_429"] = c429
    ra = (headers or {}).get("Retry-After") or (headers or {}).get("retry-after")
    try:
        wait_s = min(120.0, float(ra))
    except Exception:
        wait_s = min(120.0, float(backoff_s) * 2.0)
    wait_s += random.uniform(0.5, 2.0)  # jitter (v6.9-2)
    stop = c429 >= 2
    if stop:
        st["status"] = "rate_limited"
        wait_s = 0.0
    return wait_s, stop


# ---------------------------------------------------------------------------

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

    # v6.7 item 1: purpose-separated daily buckets — "supervisor" keeps the
    # original "calls" key (backward compatible); "eval" and "probe" get
    # their own counters AND their own caps, so a capped purpose can never
    # starve another one. Bucket = the per-provider call-count log requested
    # by v6.7-1 (state/llm-status.json daily.calls*).
    PURPOSE_KEYS = {"supervisor": "calls", "eval": "calls_eval",
                    "probe": "calls_probe"}

    def daily_count(self, provider, purpose="supervisor"):
        key = self.PURPOSE_KEYS.get(purpose, "calls")
        return int(self.daily_ensure().get(key, {}).get(provider, 0))

    def daily_add(self, provider, n=1, purpose="supervisor"):
        d = self.daily_ensure()
        key = self.PURPOSE_KEYS.get(purpose, "calls")
        bucket = d.setdefault(key, {})
        bucket[provider] = int(bucket.get(provider, 0)) + n
        return bucket[provider]

    # v6.8 item 8: failed attempts counted BY TYPE per provider per purpose
    # (daily.failed.<purpose_key>.<provider>.<err_class> = attempt count).
    # cap_reached and id_absent are NOT attempts (zero-spend) and are not
    # counted; everything that actually hit the wire and failed is.
    def daily_fail(self, provider, err_class, purpose="supervisor"):
        if not err_class or err_class in ("cap_reached", "id_absent"):
            return
        d = self.daily_ensure()
        purpose_key = self.PURPOSE_KEYS.get(purpose, "calls")
        per_provider = (d.setdefault("failed", {})
                        .setdefault(purpose_key, {})
                        .setdefault(provider, {}))
        per_provider[err_class] = int(per_provider.get(err_class, 0)) + 1

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


def write_alert(provider, st, error_class, secret_name=None):
    """outbox/ALERT-llm-<provider>.md — no secrets, error classes only.
    Idempotent (v6.4 item 4): an unchanged (status, error_class) pair never
    rewrites the file, so timestamp churn cannot retrigger the outbox path.
    auth_failed ALERTs name the missing/failed secret (appendix item 8)."""
    p = ALERTS_DIR / ("ALERT-llm-%s.md" % provider)
    alert_key = "%s:%s" % (st.get("status", "down"), error_class)
    if st.get("last_alert_key") == alert_key and p.exists():
        return
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    action = ("no automatic retry storm; the next session report opens "
              "with the providers status line")
    if error_class == "auth_failed" and secret_name:
        action += (" and names the missing/failed secret: %s "
                   "(needs_secret — skipped without retry)" % secret_name)
    else:
        action += " and names the missing/failed secret"
    body = (
        "# ALERT: LLM provider %s — %s\n\n"
        "- time: %s\n- status: %s\n- error_class: %s\n"
        "- consecutive_failures: %s\n"
        "- retry_after_s: %s\n"
        "- secret: %s\n"
        "- action: %s\n"
        % (st.get("status", "down"), provider, now_iso(),
           st.get("status", "down"), error_class,
           st.get("consecutive_failures", 0),
           st.get("retry_after_s", "n/a"),
           secret_name or "n/a",
           action)
    )
    p.write_text(body, encoding="utf-8")
    st["last_alert_key"] = alert_key


def write_all_providers_alert(detail):
    """Appendix item 8: when EVERY configured provider fell, write an
    idempotent total-failure ALERT — never hidden."""
    p = ALERTS_DIR / "ALERT-llm-all-providers.md"
    key = "all:%s" % detail
    # simple idempotence on file content: rewrite only when the detail changed
    body = (
        "# ALERT: LLM total failure — all configured providers fell\n\n"
        "- time: %s\n- detail: %s\n"
        "- action: do not retry manually; probe (scripts/llm_probe.py) will "
        "re-check each provider on the next run; the circuit breaker holds "
        "failed providers for 30 minutes\n" % (now_iso(), detail)
    )
    try:
        if p.exists() and key in p.read_text(encoding="utf-8"):
            return
    except Exception:
        pass
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def http_json(url, payload, api_key, timeout):
    """POST JSON. Returns (status, parsed|None, headers, raw_body).
    A non-JSON body does NOT raise here — the caller classifies it (no_json)
    and the diagnostics keep the first 200 chars (secret-checked)."""
    body_bytes = json.dumps(payload).encode("utf-8")
    # appendix item 13: byte-level scan of the exact outgoing payload
    hits = scan_secrets_bytes(body_bytes)
    if hits:
        raise SecretInPayload(",".join(hits))
    req = urllib.request.Request(
        url,
        data=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key,
            "User-Agent": "ginux-watch-llm-router/1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        return r.status, parsed, dict(r.headers), raw


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


def provider_timeout(cfg, prov):
    t = prov.get("request_timeout_s") or cfg.get("request_timeout_s", 120)
    return int(t)


def load_probe_gate(probe_path):
    """Returns {(provider, model): ok_bool} of the LATEST probe per pair.
    Missing file / unreadable => {} (no gating)."""
    try:
        doc = json.loads(Path(probe_path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    gate = {}
    for r in doc.get("results", []) if isinstance(doc, dict) else []:
        try:
            gate[(r["provider"], r["model"])] = bool(r.get("ok"))
        except Exception:
            continue
    return gate


def breaker_active(st):
    su = st.get("skip_until")
    return isinstance(su, (int, float)) and su > time.time()


def arm_breaker(st, cfg):
    skip_s = int(cfg.get("circuit_breaker_skip_s", 1800) or 0)
    st["skip_until"] = time.time() + skip_s
    st["skip_until_iso"] = datetime.fromtimestamp(
        st["skip_until"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def call_chat(cfg, state, system, user, meta_out, probe_path=None):
    """Try providers/models in the configured order. Returns response text;
    fills meta_out (provider, model, model_actual, latency_s, attempts).
    Raises AllProvidersFailed when nothing configured or every configured
    provider failed (a total-failure ALERT is written, item 8)."""
    providers = cfg.get("providers", [])
    attempts = int(cfg.get("attempts_per_model", 2))
    backoff = float(cfg.get("backoff_s", 5))
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))
    daily_cap = int(cfg.get("daily_call_cap_per_provider", 60) or 0)
    if probe_path is None:
        probe_path = str(DEFAULT_PROBE_STATE)
    gate = load_probe_gate(probe_path) if probe_path else {}

    configured = 0
    last_errors = []
    for prov in providers:
        name = prov["name"]
        secret_name = prov.get("env_secret", "?")
        key = os.environ.get(secret_name, "").strip()
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
        if breaker_active(st):
            last_errors.append("%s:circuit-breaker(%s)" %
                               (name, st.get("skip_until_iso", "")))
            continue
        base = prov["base_url"].rstrip("/")
        timeout = provider_timeout(cfg, prov)
        auth_broken = False
        cap_hit = False
        stop_rate_limited = False
        err_class = None
        for model in prov.get("models", []):
            if model.get("status") not in (None, "available", "unverified"):
                continue
            if model.get("enabled") is False:
                # v6.8 items 5/6: disabled secondary/paid model — never called
                # (paid models run only when the owner explicitly re-enables
                # them with a key that can pay for them)
                continue
            if gate and (name, model["id"]) in gate and not gate[(name, model["id"])]:
                last_errors.append("%s:%s:probe-failed" % (name, model["id"]))
                continue
            err_class = None
            payload = {
                "model": model["id"],
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "temperature": 0.2,
                "stream": False,
                # v6.8 item 5: explicit max_tokens on EVERY call — without it
                # OpenRouter bills the model default (131072) and free credits
                # 402 instantly ([MEASURED] excerpt200 in llm-probe.json)
                "max_tokens": int(cfg.get("supervisor_max_tokens", 3000) or 3000),
            }
            for attempt in range(1, attempts + 1):
                if daily_cap and state.daily_count(name) >= daily_cap:
                    cap_hit = True
                    err_class = "cap_reached"
                    break
                state.daily_add(name)
                throttle_provider(prov, st)  # v6.9-2: min interval 60/rpm
                t0 = time.monotonic()
                code, headers, resp, raw_body = None, {}, None, ""
                retryable = True
                ok_call = False
                rate_wait = None
                try:
                    code, resp, headers, raw_body = http_json(
                        base + "/chat/completions", payload, key, timeout)
                except urllib.error.HTTPError as e:
                    code = e.code
                    headers = dict(e.headers or {})
                    try:
                        raw_body = e.read().decode("utf-8", errors="replace")
                    except Exception:
                        raw_body = ""
                    capture_rate_limit(st, headers)
                    err_class = classify_http(code)
                    retryable = code in RETRYABLE_HTTP
                    if code == 429:
                        # v6.9-2: Retry-After (cap 120s) + jitter; a second
                        # consecutive 429 flips status to rate_limited and
                        # stops burning this provider's quota
                        rate_wait, stop429 = rate_limit_429_plan(st, headers, backoff)
                        if stop429:
                            retryable = False
                            stop_rate_limited = True
                except SecretInPayload:
                    raise
                except Exception as e:  # timeout / network
                    err_class = classify_exc(e)
                    raw_body = str(e)[:200]
                else:
                    ok_call = True
                    retryable = False
                    if resp is None:
                        retryable = True
                        err_class = "no_json"
                    else:
                        content, noncontent, model_actual = answer_and_shape(resp)
                        if content is None:
                            # v6.9-6/v7.0-4b: reasoning_exhausted (no retry)
                            # vs api_shape (retryable)
                            err_class, _fr_f, _u_f = shape_failure_class(
                                resp, int(payload.get("max_tokens") or 0))
                            retryable = err_class != "reasoning_exhausted"
                elapsed = round(time.monotonic() - t0, 2)
                if ok_call and not retryable:
                    _fr, _usg = success_shape_meta(resp)
                    st.update({
                        "status": "ok", "model_current": model["id"],
                        "model_actual": model_actual,
                        "last_success": now_iso(), "last_error_class": None,
                        "consecutive_failures": 0,
                        "consecutive_429": 0,
                        "rate_limit": extract_rate_limit(headers),
                    })
                    st.pop("skip_until", None)
                    st.pop("skip_until_iso", None)
                    st.pop("last_diag", None)
                    st.pop("last_alert_key", None)  # v6.9-3: reset on recovery
                    state.data["last_call"] = {
                        "provider": name, "model": model["id"],
                        "model_actual": model_actual,
                        "latency_s": elapsed, "outcome": "ok", "at": now_iso(),
                        "finish_reason": _fr,
                    }
                    state.save()
                    meta_out.update(provider=name, model=model["id"],
                                    model_actual=model_actual,
                                    latency_s=elapsed, attempts=attempt,
                                    retries=attempt - 1,  # v6.9-2: retries counted
                                    finish_reason=_fr, usage_summary=_usg,
                                    # v6.8 item 7: alias/free models carry
                                    # low_confidence — excluded from the
                                    # quality comparison downstream
                                    low_confidence=bool(model.get("low_confidence")))
                    return content
                # failed attempt -> diagnostics (appendix item 9) + v6.8-8
                # failed-attempt counting by type
                st["last_diag"] = diag_from_failure(
                    resp if isinstance(resp, dict) else None, code, headers,
                    raw_body, elapsed, err_class)
                state.daily_fail(name, err_class, purpose="supervisor")
                if err_class == "auth_failed":
                    st["status"] = "auth_failed"
                    st["last_error_class"] = "auth_failed"
                    st["model_current"] = model["id"]
                    state.data["last_call"] = {
                        "provider": name, "model": model["id"],
                        "outcome": "auth_failed", "at": now_iso(),
                        "diag": st["last_diag"]}
                    state.save()
                    write_alert(name, st, "auth_failed", secret_name=secret_name)
                    last_errors.append("%s:auth_failed(need:%s)" % (name, secret_name))
                    auth_broken = True
                    break  # no retry on auth errors
                if attempt < attempts:
                    time.sleep(rate_wait if rate_wait is not None else backoff)
            if auth_broken:
                break  # skip remaining models of this provider
            if stop_rate_limited:
                # v6.9-2: second consecutive 429 — provider stops burning quota
                st["last_error_class"] = "rate_limited"
                state.data["last_call"] = {
                    "provider": name, "model": model["id"],
                    "outcome": "rate_limited", "at": now_iso(),
                    "diag": st.get("last_diag")}
                state.save()
                last_errors.append("%s:rate_limited(2x429)" % name)
                break
            if cap_hit:
                st["last_error_class"] = "cap_reached"
                state.data["last_call"] = {
                    "provider": name, "outcome": "cap_reached", "at": now_iso()}
                state.save()
                last_errors.append("%s:cap_reached" % name)
                break  # provider is capped for today; stop burning models
            if err_class is None:
                continue
            # attempts exhausted for this model -> provider-level failure
            st["model_current"] = model["id"]
            st["last_error_class"] = err_class
            cf = int(st.get("consecutive_failures", 0)) + 1
            st["consecutive_failures"] = cf
            if cf >= down_threshold:
                st["status"] = "down"
                arm_breaker(st, cfg)
                write_alert(name, st, err_class)
            else:
                st["status"] = "degraded"
            state.data["last_call"] = {
                "provider": name, "model": model["id"],
                "outcome": err_class, "at": now_iso(),
                "diag": st.get("last_diag")}
            state.save()
            last_errors.append("%s:%s:%s" % (name, model["id"], err_class))
    detail = "none-configured" if configured == 0 else "all-failed:" + ";".join(last_errors[-8:])
    if configured > 0:
        write_all_providers_alert(detail)
    e = AllProvidersFailed(detail)
    e.detail = detail
    raise e


def _fail(detail):
    e = AllProvidersFailed(detail)
    e.detail = detail
    return e


def call_model(cfg, state, provider_name, model_id, system, user, meta_out):
    """Directed call to ONE (provider, model) — eval path (v6.4 items 4/6;
    appendix item 12: independent of failover order — no probe gate, no
    circuit-breaker skip, no fallback). Same timeout/attempt/backoff;
    rate-limit headers captured on success AND errors; auth_failed persists
    in status. Raises AllProvidersFailed with .detail = error class.
    v6.7 item 1: eval calls count into the SEPARATE calls_eval bucket and are
    enforced against eval_daily_call_cap_per_provider (falling back to the
    supervisor cap only for backward compatibility)."""
    prov = None
    for p in cfg.get("providers", []):
        if p.get("name") == provider_name:
            prov = p
            break
    if prov is None:
        raise _fail("unknown-provider:%s" % provider_name)
    secret_name = prov.get("env_secret", "?")
    key = os.environ.get(secret_name, "").strip()
    if not key:
        raise _fail("unconfigured:%s" % provider_name)
    st = state.ensure(provider_name)
    st["configured"] = True
    state.save()
    daily_cap = int(cfg.get("eval_daily_call_cap_per_provider",
                            cfg.get("daily_call_cap_per_provider", 60)) or 0)
    if daily_cap and state.daily_count(provider_name, purpose="eval") >= daily_cap:
        st["last_error_class"] = "cap_reached"
        state.save()
        raise _fail("cap_reached:%s" % provider_name)
    timeout = provider_timeout(cfg, prov)
    attempts = int(cfg.get("attempts_per_model", 2))
    backoff = float(cfg.get("backoff_s", 5))
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))
    base = prov["base_url"].rstrip("/")
    model_cfg = None
    for m in prov.get("models", []):
        if m.get("id") == model_id:
            model_cfg = m
            break
    payload = {
        "model": model_id,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.2,
        "stream": False,
        # v6.8 item 5: explicit max_tokens on EVERY call (eval bucket)
        "max_tokens": int(cfg.get("eval_max_tokens", 3000) or 3000),
    }
    err_class = None
    stop_rate_limited = False
    for attempt in range(1, attempts + 1):
        if daily_cap and state.daily_count(provider_name, purpose="eval") >= daily_cap:
            err_class = "cap_reached"
            break
        state.daily_add(provider_name, purpose="eval")
        throttle_provider(prov, st)  # v6.9-2: min interval 60/rpm
        t0 = time.monotonic()
        code, headers, resp, raw_body = None, {}, None, ""
        retryable = True
        ok_call = False
        rate_wait = None
        try:
            code, resp, headers, raw_body = http_json(
                base + "/chat/completions", payload, key, timeout)
        except urllib.error.HTTPError as e:
            code = e.code
            headers = dict(e.headers or {})
            raw_body = ""
            try:
                raw_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            capture_rate_limit(st, headers)
            err_class = classify_http(code)
            retryable = code in RETRYABLE_HTTP
            if code == 429:
                # v6.9-2: Retry-After (cap 120s) + jitter; second consecutive
                # 429 -> status rate_limited, stop burning quota
                rate_wait, stop429 = rate_limit_429_plan(st, headers, backoff)
                if stop429:
                    retryable = False
                    stop_rate_limited = True
        except SecretInPayload:
            raise
        except Exception as e:
            err_class = classify_exc(e)
            raw_body = str(e)[:200]
        else:
            ok_call = True
            retryable = False
            if resp is None:
                retryable = True
                err_class = "no_json"
            else:
                content, noncontent, model_actual = answer_and_shape(resp)
                if content is None:
                    # v6.9-6/v7.0-4b: reasoning_exhausted (no retry)
                    err_class, _fr_f, _u_f = shape_failure_class(
                        resp, int(payload.get("max_tokens") or 0))
                    retryable = err_class != "reasoning_exhausted"
        elapsed = round(time.monotonic() - t0, 2)
        if ok_call and not retryable:
            _fr, _usg = success_shape_meta(resp)
            st.update({
                "status": "ok", "model_current": model_id,
                "model_actual": model_actual,
                "last_success": now_iso(), "last_error_class": None,
                "consecutive_failures": 0,
                "consecutive_429": 0,
                "rate_limit": extract_rate_limit(headers),
            })
            st.pop("last_alert_key", None)  # v6.9-3: reset on recovery
            state.data["last_call"] = {
                "provider": provider_name, "model": model_id,
                "model_actual": model_actual,
                "latency_s": elapsed, "outcome": "ok", "at": now_iso(),
                "finish_reason": _fr,
            }
            state.save()
            meta_out.update(provider=provider_name, model=model_id,
                            model_actual=model_actual,
                            latency_s=elapsed, attempts=attempt,
                            retries=attempt - 1,  # v6.9-2: retries counted
                            finish_reason=_fr, usage_summary=_usg,
                            low_confidence=bool((model_cfg or {}).get("low_confidence")))
            return content
        st["last_diag"] = diag_from_failure(
            resp if isinstance(resp, dict) else None, code, headers,
            raw_body, elapsed, err_class)
        state.daily_fail(provider_name, err_class, purpose="eval")
        if err_class == "auth_failed":
            st["status"] = "auth_failed"
            st["last_error_class"] = "auth_failed"
            st["model_current"] = model_id
            state.data["last_call"] = {
                "provider": provider_name, "model": model_id,
                "outcome": "auth_failed", "at": now_iso(),
                "diag": st["last_diag"]}
            state.save()
            write_alert(provider_name, st, "auth_failed", secret_name=secret_name)
            raise _fail("auth_failed:%s" % provider_name)
        if attempt < attempts:
            time.sleep(rate_wait if rate_wait is not None else backoff)
    if stop_rate_limited:
        # v6.9-2: second consecutive 429 — provider stops burning quota
        st["last_error_class"] = "rate_limited"
        state.save()
        raise _fail("rate_limited:%s" % provider_name)
    if err_class == "cap_reached":
        st["last_error_class"] = "cap_reached"
        state.save()
        raise _fail("cap_reached:%s" % provider_name)
    cf = int(st.get("consecutive_failures", 0)) + 1
    st["consecutive_failures"] = cf
    st["model_current"] = model_id
    st["last_error_class"] = err_class
    if cf >= down_threshold:
        st["status"] = "down"
        arm_breaker(st, cfg)
        write_alert(provider_name, st, err_class)
    else:
        st["status"] = "degraded"
    state.data["last_call"] = {
        "provider": provider_name, "model": model_id,
        "outcome": err_class, "at": now_iso(),
        "diag": st.get("last_diag")}
    state.save()
    raise _fail("%s:%s:%s" % (provider_name, model_id, err_class))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system-file", required=True)
    ap.add_argument("--user-file", required=True)
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--state", default=str(DEFAULT_STATE))
    ap.add_argument("--probe-state", default=str(DEFAULT_PROBE_STATE))
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
        text = call_chat(cfg, state, system, user, meta, probe_path=args.probe_state)
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
    print("PROVIDERS: ok via %s/%s actual=%s (%ss)" %
          (meta.get("provider"), meta.get("model"),
           meta.get("model_actual"), meta.get("latency_s")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

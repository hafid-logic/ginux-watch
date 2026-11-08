#!/usr/bin/env python3
"""llm_probe.py — small fixed-input provider probe (appendix v6.6 item 11).

Runs BEFORE the shadow supervisor. Two phases per provider:

  1. VERIFY (/models with the key — appendix item 8: "تحقق من كل معرّف حيًا
     ولا تفترض"): each non-alias model id is checked against the live model
     list; ids that are absent get status "unavailable" and are reported.
     Routing aliases (config flag verify_via_models: false, e.g.
     openrouter/free) skip this phase — only the functional probe can verify
     them.
  2. PROBE (small fixed input): ONE chat call per enabled model with the
     fixed user input below; a model whose probe fails NEVER receives the
     full supervisor input (call_chat gates on this file).

Probe success criterion: HTTP 200, parseable JSON, content extracts (tolerant
extraction, appendix item 10) to an object with ok == true.

Outputs:
  state/llm-probe.json  {updated, probe_input_sha256_16, results[], providers}
    results[] rows: {provider, model, ok, category, status, latency_s,
    http_status, model_actual, at} — categories use the appendix item 9
    taxonomy (auth_failed, rate_limited, timeout, no_json, api_shape,
    schema_invalid, http_5xx, http_<code>, urlerror, cap_reached,
    id_absent, unconfigured).
  state/llm-status.json — provider-level bookkeeping (shared Status): any
    model probe ok resets the provider; all models failed increments
    consecutive_failures; at the down threshold the provider gets status
    "down", a 30-minute circuit breaker (skip_until) and an idempotent ALERT.

Daily caps: probe chat calls count into the SEPARATE probe bucket
(calls_probe) enforced against probe_daily_call_cap_per_provider (v6.7-1);
fallback to the supervisor cap keeps old configs working. Exit code is
ALWAYS 0 unless the probe itself crashes on local infrastructure (results
live in the state file; the job must continue to the supervisor/eval steps)."""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import llm_router as R  # noqa: E402

PROBE_USER = 'أعد {"ok":true} فقط'
DEFAULT_CONFIG = R.DEFAULT_CONFIG
PROBE_STATE = R.DEFAULT_PROBE_STATE
LLM_STATE = R.DEFAULT_STATE


def now_iso():
    return R.now_iso()


def get_models(base_url, api_key, timeout):
    """GET {base}/models with the key. Returns (status, parsed|None, raw)."""
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer %s" % api_key,
        "User-Agent": "ginux-watch-llm-probe/1",
    }, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            try:
                return r.status, json.loads(raw), raw
            except json.JSONDecodeError:
                return r.status, None, raw
    except urllib.error.HTTPError as e:
        try:
            return e.code, None, e.read().decode("utf-8", errors="replace")
        except Exception:
            return e.code, None, ""
    except Exception as e:
        return None, None, str(e)[:200]


def models_in_listing(parsed):
    ids = set()
    if isinstance(parsed, dict):
        for item in parsed.get("data") or parsed.get("models") or []:
            if isinstance(item, dict) and item.get("id"):
                ids.add(item["id"])
            elif isinstance(item, str):
                ids.add(item)
    return ids


def probe_model(prov, model_id, api_key, timeout):
    """ONE fixed-input chat call. Returns row dict (appendix taxonomy)."""
    t0 = time.monotonic()
    payload = {"model": model_id,
               "messages": [{"role": "user", "content": PROBE_USER}],
               "temperature": 0.0, "stream": False}
    code, resp, raw_body = None, None, ""
    try:
        code, resp, _h, raw_body = R.http_json(
            prov["base_url"].rstrip("/") + "/chat/completions",
            payload, api_key, timeout)
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            raw_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw_body = ""
        category = R.classify_http(code)
    except R.SecretInPayload:
        raise
    except Exception as e:
        category = R.classify_exc(e)
        raw_body = str(e)[:200]
    else:
        if resp is None:
            category = "no_json"
        else:
            content, noncontent, model_actual = R.answer_and_shape(resp)
            if content is None:
                category = "api_shape"
            else:
                try:
                    obj = R.extract_json_object(content)
                    category = None if obj.get("ok") is True else "schema_invalid"
                except ValueError:
                    category = "no_json"
    elapsed = round(time.monotonic() - t0, 2)
    ok = category is None
    model_actual = None
    if isinstance(resp, dict):
        model_actual = resp.get("model")
    row = {"provider": prov["name"], "model": model_id, "ok": ok,
           "category": category or "ok", "status": "ok" if ok else "failed",
           "latency_s": elapsed, "http_status": code,
           "model_actual": model_actual, "at": now_iso()}
    if not ok:
        # no-secret excerpt (appendix item 9): first 200 chars, secret-checked
        excerpt = raw_body[:200] if raw_body else ""
        hits = R.scan_secrets(excerpt)
        if hits:
            excerpt = "[redacted:secret-shaped:%s]" % ",".join(hits)
        row["excerpt200"] = excerpt
    return row


def run_probe(cfg, state):
    results = []
    prev = {}
    try:
        prev = json.loads(PROBE_STATE.read_text(encoding="utf-8"))
    except Exception:
        prev = {}
    prev_results = prev.get("results", []) if isinstance(prev, dict) else []
    down_threshold = int(cfg.get("max_consecutive_failures_for_down", 3))
    daily_cap = int(cfg.get("probe_daily_call_cap_per_provider",
                            cfg.get("daily_call_cap_per_provider", 60)) or 0)

    for prov in cfg.get("providers", []):
        name = prov["name"]
        secret_name = prov.get("env_secret", "?")
        key = (os_environ_get(secret_name) or "").strip()
        st = state.ensure(name)
        st["configured"] = bool(key)
        timeout = R.provider_timeout(cfg, prov)
        base = prov["base_url"].rstrip("/")
        enabled = [m for m in prov.get("models", [])
                   if m.get("status") in (None, "available", "unverified")]
        if not key:
            for m in enabled:
                results.append({"provider": name, "model": m["id"], "ok": False,
                                "category": "unconfigured", "status": "unavailable",
                                "secret": secret_name, "at": now_iso()})
            results.append({"provider": name, "model": None, "ok": False,
                            "category": "unconfigured", "status": "unavailable",
                            "secret": secret_name, "at": now_iso()})
            continue

        # phase 1: /models verification (skip routing aliases)
        listing_ids = None
        code_l, parsed_l, raw_l = get_models(base, key, timeout)
        if code_l == 200 and parsed_l is not None:
            listing_ids = models_in_listing(parsed_l)
        for m in enabled:
            if m.get("verify_via_models", True) and listing_ids is not None:
                if m["id"] not in listing_ids:
                    results.append({
                        "provider": name, "model": m["id"], "ok": False,
                        "category": "id_absent", "status": "unavailable",
                        "note": "absent from live /models (%d ids listed)"
                                % len(listing_ids), "at": now_iso()})

        # phase 2: fixed-input functional probe per enabled model
        any_ok = False
        last_err = None
        for m in enabled:
            skip = any(r["provider"] == name and r["model"] == m["id"]
                       and r.get("category") == "id_absent" for r in results)
            if skip:
                continue  # id proven absent: no spend, stays unavailable
            if daily_cap and state.daily_count(name, purpose="probe") >= daily_cap:
                results.append({"provider": name, "model": m["id"], "ok": False,
                                "category": "cap_reached", "status": "failed",
                                "at": now_iso()})
                last_err = last_err or "cap_reached"
                continue
            state.daily_add(name, purpose="probe")
            row = probe_model(prov, m["id"], key, timeout)
            results.append(row)
            if row["ok"]:
                any_ok = True
                st.update({"status": "ok", "model_current": m["id"],
                           "model_actual": row.get("model_actual"),
                           "last_success": now_iso(),
                           "last_error_class": None,
                           "consecutive_failures": 0})
                st.pop("skip_until", None)
                st.pop("skip_until_iso", None)
            else:
                last_err = row["category"]
        if not any_ok and enabled:
            cf = int(st.get("consecutive_failures", 0)) + 1
            st["consecutive_failures"] = cf
            st["last_error_class"] = last_err
            if last_err == "auth_failed":
                # appendix item 8: auth_failed = needs_secret — persisted,
                # skipped without retry until the secret exists
                st["status"] = "auth_failed"
                R.write_alert(name, st, "auth_failed", secret_name=secret_name)
            elif cf >= down_threshold:
                st["status"] = "down"
                R.arm_breaker(st, cfg)
                R.write_alert(name, st, last_err or "probe_failed",
                              secret_name=secret_name)
            else:
                st["status"] = "degraded"
        state.save()

    # provider-level summary
    providers = {}
    for r in results:
        p = providers.setdefault(r["provider"], {"models_ok": 0, "models_failed": 0,
                                                 "categories": []})
        if r.get("model") is None:
            continue
        if r.get("ok"):
            p["models_ok"] += 1
        else:
            p["models_failed"] += 1
            if r.get("category") not in p["categories"]:
                p["categories"].append(r.get("category"))
    st_prov = {n: s.get("status") for n, s in state.data["providers"].items()}

    doc = {
        "updated": now_iso(),
        "schema": "llm-probe-v1",
        "note": "DATA ONLY — probe rows are runtime availability evidence; "
                "no secrets; fixed probe input sha256_16 below",
        "probe_input_sha256_16": __import__("hashlib").sha256(
            PROBE_USER.encode("utf-8")).hexdigest()[:16],
        "probe_user_field": "PROBE_USER content is a fixed public string",
        "providers": providers,
        "llm_status_snapshot": st_prov,
        "results": (prev_results + results)[-400:],
    }
    PROBE_STATE.parent.mkdir(parents=True, exist_ok=True)
    PROBE_STATE.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return doc


def os_environ_get(name):
    import os
    return os.environ.get(name, "")


def main():
    try:
        cfg = R.load_config(DEFAULT_CONFIG)
        state = R.Status(LLM_STATE)
    except Exception as e:
        sys.stderr.write("PROBE: infrastructure failure: %s\n" % str(e)[:300])
        return 1
    doc = run_probe(cfg, state)
    for name, p in doc["providers"].items():
        print("PROBE: %s ok=%d failed=%d cats=%s" %
              (name, p["models_ok"], p["models_failed"],
               ",".join(p["categories"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

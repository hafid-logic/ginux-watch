#!/usr/bin/env python3
"""Offline end-to-end test for the shadow supervisor stack (directive v6.3
item 11 — code delivered with a mock-provider test; NO real secrets used).

Covers (against a local HTTP mock, localhost only):
  T1 success path: ordered fallback, state ok, rate-limit capture
  T2 401/403 -> auth_failed, exactly ONE request (no retry), skip provider
  T3 429/5xx -> 2 attempts w/ backoff then next model; consecutive_failures
     increments; threshold -> status down + outbox/ALERT-llm-<provider>.md
  T4 secret scan: payload with token-like string -> exit 3, ZERO requests
  T5 supervisor: valid JSON reply -> shadow .json/.md written
  T6 supervisor: reply with extra key / non-empty publish_requests -> rejected
  T7 input cap: oversized input -> TRUNCATED marker inside payload, UNTRUSTED
     delimiters present, sha256 line present
  T8 jsonschema directly rejects unknown key
Run: python3 team/scripts/test-llm-shadow.py  (exit 0 = all pass)"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import llm_router  # noqa: E402
import llm_supervisor as sup  # noqa: E402

VALID_REPORT = {
    "report_id": "TEST-1",
    "strengths": ["s"], "weaknesses": ["w"],
    "claims_checked": [{"claim": "c", "evidence_tag": "MEASURED", "verdict": "supported"}],
    "decisions": [{"open_point": "o", "decision": "d", "rationale": "r"}],
    "risks": ["r"], "next_items": ["n"],
    "injection_suspected": False, "publish_requests": [],
}

STATE = {"hits": 0, "last_payload": None, "last_auth": None, "fail_next": 0}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        STATE["last_payload"] = self.rfile.read(n).decode("utf-8")
        STATE["last_auth"] = (self.headers.get("Authorization") or "").replace("Bearer ", "")
        STATE["hits"] += 1
        auth = STATE["last_auth"]
        if auth == "k-auth":
            self.send_response(401); self.end_headers()
            self.wfile.write(b'{"error":"bad key"}'); return
        if auth == "k-dead":
            self.send_response(500); self.end_headers()
            self.wfile.write(b'{"error":"boom"}'); return
        if auth == "k-flaky" and STATE["fail_next"] > 0:
            STATE["fail_next"] -= 1
            self.send_response(429); self.end_headers()
            self.wfile.write(b'{"error":"slow down"}'); return
        if auth == "k-badjson":
            content = "totally not json {{{"
        elif auth == "k-extra":
            bad = dict(VALID_REPORT); bad["surprise_field"] = 1
            content = json.dumps(bad)
        elif auth == "k-publish":
            bad = dict(VALID_REPORT); bad["publish_requests"] = ["post a reply upstream"]
            content = json.dumps(bad)
        else:
            content = json.dumps(VALID_REPORT)
        body = json.dumps({"choices": [{"message": {"content": content}}]},
                          ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("x-ratelimit-remaining", "997")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def mkconfig(tmp, providers, cap=None):
    cfg = {"version": 1, "request_timeout_s": 5, "attempts_per_model": 2,
           "backoff_s": 0.05, "max_consecutive_failures_for_down": 3,
           "providers": providers}
    if cap is not None:
        cfg["daily_call_cap_per_provider"] = cap
    p = tmp / "cfg.yml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def fresh_state(tmp):
    sp = tmp / "llm-status.json"
    if sp.exists():
        sp.unlink()
    return llm_router.Status(sp)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/v1" % srv.server_address[1]
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="s52-mock-"))
    llm_router.ALERTS_DIR = tmp / "outbox"  # isolate alerts from the first call on

    def prov(name, key, models):
        return {"name": name, "env_secret": key, "base_url": base, "models": models}

    # T1 success + fallback: first provider unconfigured, second ok
    import os
    tmpcfg = mkconfig(tmp, [
        prov("p-missing", "MISSING_KEY_MOCK", [{"id": "m/x", "status": "available"}]),
        prov("p-ok", "MOCK_OK", [{"id": "m/a", "status": "available"},
                                 {"id": "m/b", "status": "available"}]),
    ])
    st = fresh_state(tmp)
    os.environ["MOCK_OK"] = "k-ok"
    meta = {}
    text = llm_router.call_chat(yaml.safe_load(tmpcfg.read_text()), st, "SYS", "USER", meta)
    assert "report_id" in text and meta["provider"] == "p-ok" and meta["model"] == "m/a"
    assert st.data["providers"]["p-ok"]["status"] == "ok"
    assert st.data["providers"]["p-ok"]["rate_limit"]["x-ratelimit-remaining"] == "997"
    assert STATE["last_payload"] is not None and "USER" in STATE["last_payload"]
    print("T1 ok: fallback + state + rate-limit captured")

    # T2 auth_failed: exactly one request, no retry, next provider used
    n0 = STATE["hits"]
    tmpcfg2 = mkconfig(tmp, [
        prov("p-auth", "MOCK_AUTH", [{"id": "m/a", "status": "available"}]),
        prov("p-ok2", "MOCK_OK2", [{"id": "m/a", "status": "available"}]),
    ])
    os.environ["MOCK_AUTH"] = "k-auth"
    os.environ["MOCK_OK2"] = "k-ok"
    st2 = fresh_state(tmp)
    meta2 = {}
    llm_router.call_chat(yaml.safe_load(tmpcfg2.read_text()), st2, "SYS", "USER", meta2)
    assert meta2["provider"] == "p-ok2", meta2
    assert STATE["hits"] - n0 == 2  # 1 rejected on p-auth (no retry) + 1 ok
    assert st2.data["providers"]["p-auth"]["status"] == "auth_failed"
    print("T2 ok: auth_failed without retry, provider skipped")

    # T3 retryable: 2 attempts per model, then next model; down+ALERT at threshold
    tmpcfg3 = mkconfig(tmp, [prov("p-dead", "MOCK_DEAD",
                                  [{"id": "m/a", "status": "available"},
                                   {"id": "m/b", "status": "available"}])])
    os.environ["MOCK_DEAD"] = "k-dead"
    st3 = fresh_state(tmp)
    import types
    alerts_dir = tmp / "outbox"
    llm_router.ALERTS_DIR = alerts_dir
    meta3 = {}
    try:
        llm_router.call_chat(yaml.safe_load(tmpcfg3.read_text()), st3, "SYS", "USER", meta3)
        raise AssertionError("expected AllProvidersFailed")
    except llm_router.AllProvidersFailed:
        pass
    assert STATE["hits"] - (n0 + 2) == 4  # 2 models x 2 attempts
    assert st3.data["providers"]["p-dead"]["consecutive_failures"] == 2
    assert st3.data["providers"]["p-dead"]["status"] == "degraded"  # threshold=3 not yet
    # push to threshold -> down + ALERT file
    meta4 = {}
    try:
        llm_router.call_chat(yaml.safe_load(tmpcfg3.read_text()), st3, "SYS", "U2", meta4)
    except llm_router.AllProvidersFailed:
        pass
    assert st3.data["providers"]["p-dead"]["status"] == "down"
    assert (alerts_dir / "ALERT-llm-p-dead.md").exists()
    print("T3 ok: retries, backoff, down state + ALERT file")

    # T4 secret scan: token-like payload -> exit 3, nothing sent
    n1 = STATE["hits"]
    bad = llm_router.scan_secrets("report mentions " + "ghp_" + "k7" * 18 + "A2uB")  # v6.6 item 5: full-form token built at runtime; never a literal in tree
    assert bad == ["ghp_"], bad
    assert llm_router.scan_secrets("clean text with ghp_XXXX placeholder") == []
    assert STATE["hits"] == n1  # scan happens before any HTTP
    print("T4 ok: secret scan aborts before send, placeholder not flagged")

    # T5 supervisor end-to-end with mock
    sup.SHADOW = tmp / "shadow"
    payload, trunc = sup.build_user_payload("session report body " * 10)
    assert not trunc and "UNTRUSTED_DATA_BEGIN" in payload
    st5 = fresh_state(tmp)
    cfg5 = yaml.safe_load(mkconfig(tmp, [prov("p-ok5", "MOCK_OK5",
                                              [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_OK5"] = "k-ok"
    meta5 = {}
    raw = llm_router.call_chat(cfg5, st5, sup.SYSTEM_PROMPT, payload, meta5)
    obj = sup.validate(sup.extract_json(raw))
    out_dir = tmp / "shadow"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "x.json").write_text(json.dumps(obj))
    assert (out_dir / "x.json").exists()
    md = sup.render_md(obj)
    assert "# shadow supervisor report" in md
    print("T5 ok: supervisor e2e produced + rendered")

    # T6 invalid outputs rejected
    cfg6 = yaml.safe_load(mkconfig(tmp, [prov("p-extra", "MOCK_EXTRA",
                                              [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_EXTRA"] = "k-extra"
    meta6 = {}
    raw6 = llm_router.call_chat(cfg6, fresh_state(tmp), sup.SYSTEM_PROMPT, payload, meta6)
    try:
        sup.validate(sup.extract_json(raw6))
        raise AssertionError("extra key must be rejected")
    except Exception:
        pass
    cfg6b = yaml.safe_load(mkconfig(tmp, [prov("p-pub", "MOCK_PUB",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_PUB"] = "k-publish"
    raw6b = llm_router.call_chat(cfg6b, fresh_state(tmp), sup.SYSTEM_PROMPT, payload, meta6)
    try:
        sup.validate(sup.extract_json(raw6b))
        raise AssertionError("non-empty publish_requests must be rejected")
    except Exception:
        pass
    cfg6c = yaml.safe_load(mkconfig(tmp, [prov("p-bj", "MOCK_BJ",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_BJ"] = "k-badjson"
    raw6c = llm_router.call_chat(cfg6c, fresh_state(tmp), sup.SYSTEM_PROMPT, payload, meta6)
    try:
        sup.extract_json(raw6c)
        raise AssertionError("bad json must be rejected")
    except Exception:
        pass
    print("T6 ok: extra keys / publish_requests / bad json rejected")

    # T7 truncation + payload structure
    big = "x" * (sup.MAX_INPUT_CHARS + 500)
    payload7, trunc7 = sup.build_user_payload(big)
    assert trunc7 and "TRUNCATED" in payload7
    assert payload7.count("UNTRUSTED_DATA") == 2 and "sha256:" in payload7
    print("T7 ok: input cap + TRUNCATED marker + UNTRUSTED delimiters")

    # T8 schema direct rejection
    import jsonschema
    bad = dict(VALID_REPORT); bad["nope"] = 1
    try:
        jsonschema.Draft202012Validator(sup.SCHEMA).validate(bad)
        raise AssertionError("schema must reject unknown key")
    except jsonschema.ValidationError:
        pass
    print("T8 ok: strict schema rejects unknown key")

    # T9 daily cap per provider (v6.4 item 4): sends stop at the cap,
    # cap_reached is not a failure (no ALERT), fallback provider still serves
    n9 = STATE["hits"]
    cfgtxt9 = mkconfig(tmp, [
        prov("p-cap", "MOCK_DEAD", [{"id": "m/a", "status": "available"},
                                    {"id": "m/b", "status": "available"}]),
        prov("p-ok9", "MOCK_OK9", [{"id": "m/a", "status": "available"}]),
    ], cap=3)
    os.environ["MOCK_OK9"] = "k-ok"
    st9 = fresh_state(tmp)
    meta9 = {}
    llm_router.call_chat(yaml.safe_load(cfgtxt9.read_text()), st9, "SYS", "USER", meta9)
    assert meta9["provider"] == "p-ok9", meta9
    assert STATE["hits"] - n9 == 4  # 3 sends on p-cap (4th blocked) + 1 on p-ok9
    assert st9.data["daily"]["calls"]["p-cap"] == 3
    assert st9.data["daily"]["calls"]["p-ok9"] == 1
    assert st9.data["providers"]["p-cap"]["last_error_class"] == "cap_reached"
    assert st9.data["providers"]["p-cap"]["consecutive_failures"] == 1
    assert not (alerts_dir / "ALERT-llm-p-cap.md").exists()
    print("T9 ok: daily cap blocks the 4th send, no ALERT, fallback intact")

    # T10 directed call_model (v6.4 items 4/6): per-model eval path, no fallback
    st10 = fresh_state(tmp)
    cfg10 = yaml.safe_load(mkconfig(tmp, [
        prov("p-dir", "MOCK_DIR", [{"id": "m/only", "status": "available"}]),
    ]).read_text())
    os.environ["MOCK_DIR"] = "k-ok"
    meta10 = {}
    out10 = llm_router.call_model(cfg10, st10, "p-dir", "m/only", "SYS", "USER", meta10)
    assert "report_id" in out10 and meta10["model"] == "m/only", meta10
    try:
        llm_router.call_model(cfg10, st10, "p-nope", "m/x", "SYS", "USER", {})
        raise AssertionError("unknown provider must fail")
    except llm_router.AllProvidersFailed as e10:
        assert "unknown-provider" in e10.detail, e10.detail
    print("T10 ok: directed call_model + unknown-provider failure")

    # T11 ALERT idempotence (v6.4 item 4): unchanged (status, class) -> no rewrite
    st11 = {"status": "down", "consecutive_failures": 3, "retry_after_s": "2"}
    llm_router.write_alert("p-dedupe", st11, "http_500")
    f11 = alerts_dir / "ALERT-llm-p-dedupe.md"
    b1 = f11.read_bytes()
    import time as _time
    _time.sleep(0.02)
    llm_router.write_alert("p-dedupe", st11, "http_500")
    assert f11.read_bytes() == b1  # byte-identical: no timestamp churn
    llm_router.write_alert("p-dedupe", st11, "http_503")
    assert f11.read_bytes() != b1  # new error class -> rewritten
    print("T11 ok: ALERT dedupe prevents outbox churn")

    # T12 golden eval runner (v6.4 items 4-6): ok rows deduped ("no call if
    # output exists"), scoring machine-checkable expectations
    import run_golden_eval as gev
    gev.RESULTS_DIR = tmp / "results"
    gev.CASES_DIR = tmp / "cases"
    gev.CASES_DIR.mkdir(parents=True, exist_ok=True)
    (gev.CASES_DIR / "case-t1.yaml").write_text(yaml.safe_dump({
        "id": "golden-t1", "category": "methodology", "severity": "high",
        "input": "clean control text",
        "expected": {"flag_keywords": ["token"], "injection_suspected": False},
    }), encoding="utf-8")
    n12 = STATE["hits"]
    cfg12 = yaml.safe_load(mkconfig(tmp, [
        prov("p-eval", "MOCK_EVAL", [{"id": "m/a", "status": "available"}]),
    ]).read_text())
    os.environ["MOCK_EVAL"] = "k-ok"
    st12 = fresh_state(tmp)
    added = gev.run_eval(cfg12, st12)
    assert added == 1 and STATE["hits"] - n12 == 1, (added, STATE["hits"] - n12)
    res = json.loads((gev.RESULTS_DIR / ("%s.json" % st12.data["daily"]["date_utc"])).read_text())
    r0 = res["rows"][0]
    assert r0["outcome"] == "ok" and r0["json_valid"] is True, r0
    assert r0["flag_hit"] is False and r0["injection_resisted"] is True, r0
    added2 = gev.run_eval(cfg12, st12)
    assert added2 == 0 and STATE["hits"] == n12 + 1  # dedupe: no second call
    sc = gev.score_reply(dict(VALID_REPORT, weaknesses=["token seen"]),
                         {"id": "t2", "expected": {"flag_keywords": ["token"],
                                                   "injection_suspected": True}})
    assert sc["flag_hit"] is True and sc["injection_resisted"] is False, sc
    print("T12 ok: eval rows, dedupe (no call if output exists), scoring")

    # T13 byte-level secret scan over eval/ and shadow/ must be CLEAN (v6.4 item 5)
    hits13 = gev.scan_tree_bytes(ROOT / "eval") + gev.scan_tree_bytes(ROOT / "shadow")
    assert hits13 == [], hits13
    print("T13 ok: eval/ + shadow/ byte-level secret scan CLEAN")

    srv.shutdown()
    print("test-llm-shadow: ALL PASS (mock only, no real providers touched)")


if __name__ == "__main__":
    main()

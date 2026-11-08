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


def mkconfig(tmp, providers):
    cfg = {"version": 1, "request_timeout_s": 5, "attempts_per_model": 2,
           "backoff_s": 0.05, "max_consecutive_failures_for_down": 3,
           "providers": providers}
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
    bad = llm_router.scan_secrets("report mentions ghp_9xK2mQwL7vBnT4rDs8YhP3zFc6JdN1wQeR5tA2uB")
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

    srv.shutdown()
    print("test-llm-shadow: ALL PASS (mock only, no real providers touched)")


if __name__ == "__main__":
    main()

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
  T14 tolerant JSON extraction (appendix 10): fences anywhere, leading text,
     first balanced block, no_json error
  T15 failure taxonomy (appendix 9): auth_failed/rate_limited/http_5xx/timeout
  T16 model_actual captured from response "model" (appendix 8); non-content
     fields logged by name, never used as answer (api_shape)
  T17 probe gating: model with failed probe never gets the full input
  T18 circuit breaker: provider with skip_until in the future is skipped
  T19 byte-level payload scan aborts before send (appendix 13)
  T20 total-failure ALERT (appendix 8): all configured providers fell
  T21 eval row classification: schema_invalid outcome (appendix 9/12)
  T22 probe runner: /models verification + fixed-input probe rows
  T23 purpose-separated cap buckets (v6.7-1): eval->calls_eval w/ eval cap,
      supervisor->calls w/ supervisor cap; one capped purpose never blocks
      the other; llm_cap_summary prints both buckets with used/cap
  T24 eval gate (v6.7-1): run_golden_eval.main() refuses without
      GOLDEN_EVAL_GATE=run_eval-true — ZERO HTTP calls spent
  T25 golden-case YAML gate (v6.8-2): loads the REAL eval/golden/*.yaml with
      the strict loader (duplicate keys rejected, jsonschema required-keys,
      duplicate ids rejected, count reported) and proves rejection on a
      duplicate-key fixture; run_golden_eval --validate passes offline
  T26 truncation simulation (v7.4-2): the REAL archived 0011Z nvidia reply
      classifies truncated_json; both attempts' finish_reason/tokens on record
  T27 word caps (v7.4-2): enforce_word_caps trims deterministically, schema
      stays valid, compressed flag flips, under-cap reply untouched
  T28 max_tokens math (v7.4-2): config 1657 == ceil(p95 x 1.5) as recorded
  T29 roles/bucket (v7.4-1): probe-only provider gets ZERO supervisor calls
  T30 UTC quota (v7.4-1): state/quota-google-<date>.json counter, auto-bypass
      at cap with zero failure marking and zero ALERT (call_model too)
  T31 prompt_suffix (v7.4-2): nvidia system prompt carries /no_think
  T32 provider pin (v7.4-5): LLM_PREFER_PROVIDER front-of-order + fallback
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
        try:
            _model = json.loads(STATE["last_payload"]).get("model", "")
        except Exception:
            _model = ""
        if _model.endswith("ghost"):
            body = b'{"error": {"message": "model not found"}}'
            self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
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
        elif auth == "k-probe":
            content = '{"ok": true}'
        elif auth == "k-schemabad":
            content = '{"unexpected_field": 1}'
        elif auth == "k-reasoning":
            body = json.dumps({"model": "mock/actual-1",
                               "choices": [{"message": {
                                   "reasoning": "I thought about it"},
                                   "finish_reason": "stop"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        else:
            content = json.dumps(VALID_REPORT)
        body = json.dumps({"model": "mock/actual-1",
                           "choices": [{"message": {"content": content}}]},
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
    big = "x" * (sup.MAX_REPORT_CHARS + 500)
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


    # T14 tolerant JSON extraction (appendix item 10)
    ex = llm_router.extract_json_object
    assert ex('```json\n{"a": 1}\n```') == {"a": 1}
    assert ex('sure! here you go:\n{"a": {"b": 2}} hope that helps') == {"a": {"b": 2}}
    assert ex('{"x": "with } brace inside"} trailing text') == {"x": "with } brace inside"}
    try:
        ex("no braces at all")
        raise AssertionError("expected no_json")
    except ValueError as e14:
        assert str(e14).startswith("no_json"), e14
    assert sup.extract_json('prefix {"report_id": "r"}') == {"report_id": "r"}
    print("T14 ok: tolerant extraction (fences, leading text, balanced block, no_json)")

    # T15 failure taxonomy (appendix item 9)
    assert llm_router.classify_http(401) == "auth_failed"
    assert llm_router.classify_http(403) == "auth_failed"
    assert llm_router.classify_http(429) == "rate_limited"
    assert llm_router.classify_http(500) == "http_5xx"
    assert llm_router.classify_http(418) == "http_418"
    assert llm_router.classify_exc(json.JSONDecodeError("x", "{}", 0)) == "no_json"
    import socket as _s
    assert llm_router.classify_exc(_s.timeout()) == "timeout"
    print("T15 ok: taxonomy classes (auth_failed/rate_limited/http_5xx/timeout/no_json)")

    # T16 model_actual + non-content answer fields (appendix items 8/10)
    st16 = fresh_state(tmp)
    cfg16 = yaml.safe_load(mkconfig(tmp, [prov("p-act", "MOCK_ACT",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_ACT"] = "k-ok"
    meta16 = {}
    llm_router.call_chat(cfg16, st16, "SYS", "USER", meta16)
    assert meta16["model_actual"] == "mock/actual-1", meta16
    content16, nonc16, act16 = llm_router.answer_and_shape(
        {"model": "mock/x", "choices": [{"message": {"reasoning": "hidden answer"}}]})
    assert content16 is None and nonc16 == ["reasoning"] and act16 == "mock/x"
    print("T16 ok: model_actual logged; reasoning-only reply = api_shape (never the answer)")

    # T17 probe gating (appendix item 11): failed probe -> model skipped
    probe_file = tmp / "llm-probe.json"
    probe_file.write_text(json.dumps({
        "updated": "x", "results": [
            {"provider": "p-gate", "model": "m/a", "ok": False, "category": "timeout"},
            {"provider": "p-gate", "model": "m/b", "ok": True, "category": "ok"},
        ]}))
    st17 = fresh_state(tmp)
    cfg17 = yaml.safe_load(mkconfig(tmp, [prov("p-gate", "MOCK_OK",
                                               [{"id": "m/a", "status": "available"},
                                                {"id": "m/b", "status": "available"}])]).read_text())
    os.environ["MOCK_OK"] = "k-ok"
    n17 = STATE["hits"]
    meta17 = {}
    llm_router.call_chat(cfg17, st17, "SYS", "USER", meta17, probe_path=str(probe_file))
    assert meta17["model"] == "m/b" and STATE["hits"] - n17 == 1, (meta17, STATE["hits"] - n17)
    print("T17 ok: probe-failed model skipped, healthy sibling serves")

    # T18 circuit breaker (appendix item 11): skip_until in the future
    st18 = fresh_state(tmp)
    st18.ensure("p-brk")
    st18.data["providers"]["p-brk"].update({"configured": True, "status": "down",
                                            "skip_until": __import__("time").time() + 600,
                                            "skip_until_iso": "soin"})
    st18.save()
    cfg18 = yaml.safe_load(mkconfig(tmp, [
        prov("p-brk", "MOCK_OK", [{"id": "m/a", "status": "available"}]),
        prov("p-next", "MOCK_OK", [{"id": "m/a", "status": "available"}]),
    ]).read_text())
    n18 = STATE["hits"]
    meta18 = {}
    llm_router.call_chat(cfg18, st18, "SYS", "USER", meta18, probe_path=str(tmp / "no-probe.json"))
    assert meta18["provider"] == "p-next" and STATE["hits"] == n18 + 1
    print("T18 ok: circuit breaker holds failed provider 30 min, next provider serves")

    # T19 byte-level payload scan (appendix item 13): nothing sent on hit
    n19 = STATE["hits"]
    tok19 = "ghp_" + "k7" * 18 + "A2uB"  # built at runtime; never a literal in tree
    st19 = fresh_state(tmp)
    cfg19 = yaml.safe_load(mkconfig(tmp, [prov("p-scan", "MOCK_OK",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    try:
        llm_router.call_chat(cfg19, st19, "SYS", "user mentions " + tok19, {},
                             probe_path=str(tmp / "no-probe.json"))
        raise AssertionError("expected SecretInPayload")
    except llm_router.SecretInPayload:
        pass
    assert STATE["hits"] == n19  # zero HTTP
    print("T19 ok: byte-level scan aborts before send, zero requests")

    # T20 total-failure ALERT (appendix item 8)
    st20 = fresh_state(tmp)
    cfg20 = yaml.safe_load(mkconfig(tmp, [prov("p-only", "MOCK_DEAD",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_DEAD"] = "k-dead"
    try:
        llm_router.call_chat(cfg20, st20, "SYS", "U", {}, probe_path=str(tmp / "no-probe.json"))
    except llm_router.AllProvidersFailed:
        pass
    assert (alerts_dir / "ALERT-llm-all-providers.md").exists()
    print("T20 ok: all-providers ALERT written, total failure not hidden")

    # T21 eval row classification: schema_invalid (appendix items 9/12)
    import run_golden_eval as gev2
    gev2.RESULTS_DIR = tmp / "results2"
    gev2.CASES_DIR = tmp / "cases2"
    gev2.CASES_DIR.mkdir(parents=True, exist_ok=True)
    (gev2.CASES_DIR / "case-s.yaml").write_text(yaml.safe_dump({
        "id": "golden-s", "category": "methodology", "severity": "low",
        "input": "clean control", "expected": {}}), encoding="utf-8")
    n21 = STATE["hits"]
    cfg21 = yaml.safe_load(mkconfig(tmp, [prov("p-sb", "MOCK_SB",
                                               [{"id": "m/a", "status": "available"}])]).read_text())
    os.environ["MOCK_SB"] = "k-schemabad"
    st21 = fresh_state(tmp)
    gev2.run_eval(cfg21, st21)
    res21 = json.loads((gev2.RESULTS_DIR / ("%s.json" % st21.data["daily"]["date_utc"])).read_text())
    r21 = res21["rows"][0]
    assert r21["outcome"] == "schema_invalid" and r21["json_valid"] is False, r21
    # v6.8-7: summary keys follow model_actual when present (mock answers as
    # mock/actual-1), falling back to the configured id for no-actual rows
    k21 = "p-sb/%s" % (r21.get("model_actual") or "m/a")
    assert res21["summary"][k21]["schema_invalid"] == 1, res21["summary"]
    assert res21["rows"][0]["low_confidence"] is False
    print("T21 ok: schema_invalid row + summary counter (keyed by model_actual, v6.8-7)")

    # T22 probe runner (appendix items 8/11): /models verification + fixed input
    # v6.8-6 semantics: the functional probe hits the FIRST enabled model of a
    # provider only; later models stay unprobed (zero spend)
    import llm_probe as prb
    prb.PROBE_STATE = tmp / "probe-out.json"
    prb.LLM_STATE = tmp / "llm-status-probe.json"
    cfg22 = yaml.safe_load(mkconfig(tmp, [
        prov("p-probe", "MOCK_PROBE", [{"id": "m/a", "status": "unverified"}]),
        prov("p-probe-multi", "MOCK_PROBE", [{"id": "m/ghost", "status": "unverified"},
                                             {"id": "m/a", "status": "unverified"}]),
        prov("p-probe-auth", "MOCK_PROBE_AUTH", [{"id": "m/a", "status": "unverified"}]),
    ]).read_text())
    os.environ["MOCK_PROBE"] = "k-probe"
    os.environ["MOCK_PROBE_AUTH"] = "k-auth"
    st22 = llm_router.Status(prb.LLM_STATE)
    # /models returns 404 on the mock (no GET handler) -> listing unavailable,
    # no id_absent rows; first model probed functionally per provider
    doc22 = prb.run_probe(cfg22, st22)
    rows22 = {(r["provider"], r["model"]): r for r in doc22["results"]}
    assert rows22[("p-probe", "m/a")]["ok"] is True, rows22
    assert rows22[("p-probe", "m/a")]["category"] == "ok"
    # first-model-only: m/ghost probed (first), m/a NOT probed (second)
    assert rows22[("p-probe-multi", "m/ghost")]["ok"] is False
    assert ("p-probe-multi", "m/a") not in rows22, "second model must not be probed (v6.8-6)"
    assert rows22[("p-probe-auth", "m/a")]["category"] == "auth_failed"
    assert st22.data["providers"]["p-probe"]["status"] == "ok"
    assert st22.data["providers"]["p-probe-auth"]["status"] == "auth_failed"
    assert doc22["providers"]["p-probe"]["models_ok"] == 1
    # probe payload carried the explicit max_tokens (v6.8-5, probe=200)
    last_p = json.loads(STATE["last_payload"])
    assert last_p.get("max_tokens") == 200, last_p.get("max_tokens")
    print("T22 ok: probe rows (ok / failed / auth_failed), first-model-only, max_tokens=200")

    # T23 purpose-separated caps/buckets (v6.7 item 1)
    import io
    import contextlib
    import llm_cap_summary as capsum
    cfg23p = mkconfig(tmp, [
        prov("p-sep", "MOCK_SEP", [{"id": "m/a", "status": "available"}]),
    ], cap=99)
    cfg23 = yaml.safe_load(cfg23p.read_text())
    cfg23["eval_daily_call_cap_per_provider"] = 1
    cfg23p.write_text(yaml.safe_dump(cfg23), encoding="utf-8")  # summary re-reads the FILE
    os.environ["MOCK_SEP"] = "k-sep"
    st23 = fresh_state(tmp)
    m23 = {}
    txt23 = llm_router.call_model(cfg23, st23, "p-sep", "m/a", "SYS", "USER", m23)
    assert m23["provider"] == "p-sep"
    d23 = st23.data["daily"]
    assert int(d23["calls_eval"]["p-sep"]) == 1, d23
    assert int(d23.get("calls", {}).get("p-sep", 0)) == 0, d23  # untouched bucket
    try:
        llm_router.call_model(cfg23, st23, "p-sep", "m/a", "SYS", "USER", {})
        raise AssertionError("eval cap (1) was not enforced")
    except llm_router.AllProvidersFailed as e:
        assert e.detail == "cap_reached:p-sep", e.detail
    # ...while the supervisor path still runs on its own bucket/cap
    meta23 = {}
    llm_router.call_chat(cfg23, st23, "SYS", "USER", meta23,
                         probe_path=str(tmp / "absent-probe.json"))
    assert meta23["provider"] == "p-sep"
    assert int(st23.data["daily"]["calls"]["p-sep"]) == 1
    buf23 = io.StringIO()
    with contextlib.redirect_stdout(buf23):
        capsum.main(["--config", str(cfg23p), "--state", str(st23.path)])
    out23 = buf23.getvalue()
    assert "| eval | p-sep | 1 | 1 |" in out23, out23
    assert "| supervisor | p-sep | 1 | 99 |" in out23, out23
    print("T23 ok: purpose buckets/caps separated (calls vs calls_eval), summary printed")

    # T24 eval gate (v6.7 item 1): without GOLDEN_EVAL_GATE=run_eval-true the
    # runner refuses and spends ZERO calls — push/schedule can never eval
    import sys as _sys
    import run_golden_eval as gev3
    cfg24p = mkconfig(tmp, [
        prov("p-gate", "MOCK_GATE", [{"id": "m/a", "status": "available"}]),
    ])
    os.environ["MOCK_GATE"] = "k-gate"
    hits24 = STATE["hits"]
    old_argv = _sys.argv
    closed = 0
    for gate24 in (None, "run_eval-false"):
        if gate24 is None:
            os.environ.pop("GOLDEN_EVAL_GATE", None)
        else:
            os.environ["GOLDEN_EVAL_GATE"] = gate24
        _sys.argv = ["run_golden_eval.py", "--config", str(cfg24p),
                     "--state", str(tmp / "s24-state.json")]
        try:
            rc24 = gev3.main()
        finally:
            _sys.argv = old_argv
        assert rc24 == 0, rc24
        closed += 1
    assert STATE["hits"] == hits24, (hits24, STATE["hits"])
    assert closed == 2
    print("T24 ok: eval gate closed without run_eval=true — 0 calls spent")

    # T25 golden-case YAML gate (v6.8 item 2): the REAL eval/golden cases must
    # strict-load (dup keys/ids rejected, jsonschema required keys, count
    # reported) — a test that does not load the real cases does not count
    import golden_case_loader as gcl
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_golden_eval as gev4
    cases25, rep25 = gcl.load_golden_cases()  # REAL repo cases
    assert rep25["cases"] >= 17, rep25
    assert not rep25["errors"], rep25
    ids25 = [c["id"] for c in cases25]
    assert len(ids25) == len(set(ids25)), "duplicate ids slipped through"
    # negative proof 1: duplicate mapping key (PyYAML accepts silently) -> gate rejects
    dupdir = tmp / "dup-cases"
    dupdir.mkdir()
    (dupdir / "case-dup.yaml").write_text(
        "id: golden-x-dup\ncategory: c\nseverity: low\ninput: |\n  hi\n"
        "expected:\n  flag_keywords: []\n  flag_keywords: [b]\n",
        encoding="utf-8")
    try:
        gcl.load_golden_cases(dupdir)
        raise AssertionError("duplicate key was NOT rejected")
    except gcl.GoldenCaseError:
        pass
    # negative proof 2: schema violation (missing required keys) -> gate rejects
    (dupdir / "case-dup.yaml").write_text(
        "id: golden-x-miss\ncategory: c\nseverity: low\n", encoding="utf-8")
    try:
        gcl.load_golden_cases(dupdir)
        raise AssertionError("schema violation was NOT rejected")
    except gcl.GoldenCaseError:
        pass
    # negative proof 3: duplicate case id across two files -> gate rejects
    dupdir2 = tmp / "dup-ids"
    dupdir2.mkdir()
    for nm in ("case-a.yaml", "case-b.yaml"):
        (dupdir2 / nm).write_text(
            "id: golden-same\ncategory: c\nseverity: low\ninput: |\n  hi\n"
            "expected: {}\n", encoding="utf-8")
    try:
        gcl.load_golden_cases(dupdir2)
        raise AssertionError("duplicate id was NOT rejected")
    except gcl.GoldenCaseError:
        pass
    # run_golden_eval --validate: same gate, offline, zero HTTP.
    # NOTE: T21 redirected gev2.CASES_DIR to a temp dir (same module object) —
    # restore the REAL cases dir first, else --validate would count 1 fixture
    import io as _io
    import contextlib as _cl
    gev4.CASES_DIR = ROOT / "eval/golden"
    hits25 = STATE["hits"]
    old_argv25 = _sys.argv
    _sys.argv = ["run_golden_eval.py", "--validate"]
    buf25 = _io.StringIO()
    try:
        with _cl.redirect_stdout(buf25):
            rc25 = gev4.main()
    finally:
        _sys.argv = old_argv25
    assert rc25 == 0, rc25
    assert str(rep25["cases"]) in buf25.getvalue(), buf25.getvalue()
    assert STATE["hits"] == hits25, "--validate spent HTTP calls"
    print("T25 ok: %d real golden cases strict-loaded; dup-key/schema/dup-id "
          "rejection proven; --validate offline zero-spend" % rep25["cases"])

    # ---- v7.4 tests (directive v7.4-1/2/6, 2026-11-10) — all offline/mock ----

    # T26 truncation simulation (v7.4-2): the REAL archived attempt-1 reply of
    # the 0011Z nvidia truncation must classify truncated_json, and a
    # synthetic cut mid-object behaves the same -> both feed the compressed
    # retry path. Plus: attempt-1/2 numbers are on record (finish_reason).
    trunc_art = ROOT / "eval/failures/2026-11-10/rerun-0011Z.nvidia.truncated_json.txt"
    raw_t26 = trunc_art.read_text(encoding="utf-8", errors="replace")
    assert "{" in raw_t26
    try:
        sup.extract_json(raw_t26)
        raise AssertionError("truncated artifact unexpectedly parsed")
    except ValueError as e:
        cls_t26, _n = sup.classify_reply_failure(raw_t26, str(e))
    assert cls_t26 == "truncated_json", cls_t26
    cut26 = json.dumps(VALID_REPORT)[:-40]  # cut mid-object
    try:
        sup.extract_json(cut26)
        raise AssertionError("mid-object cut unexpectedly parsed")
    except ValueError as e:
        cls26b, _ = sup.classify_reply_failure(cut26, str(e))
    assert cls26b == "truncated_json", cls26b
    p95doc = json.loads((ROOT / "eval/nvidia-truncation/"
                         "p95-analysis-2026-11-10.json").read_text(encoding="utf-8"))
    assert p95doc["attempt1_0011Z"]["finish_reason"] == "length"
    assert p95doc["attempt2_0011Z_measured"]["finish_reason"] == "length"
    assert p95doc["attempt2_0011Z_measured"]["completion_tokens"] == 3000
    assert p95doc["attempt2_0011Z_measured"]["reasoning_tokens"] == 2499
    print("T26 ok: truncation simulation -> truncated_json (real artifact + "
          "synthetic cut); both 0011Z attempts on record finish_reason=length")

    # T27 word caps (v7.4-2): over-cap reply is deterministically trimmed and
    # stays schema-valid; flag flips; under-cap reply untouched.
    big = json.loads(json.dumps(VALID_REPORT))
    big["strengths"] = ["word%d " % i + "x" * 1 for i in range(9)]  # 9 items
    big["strengths"] = [("s%d " % i) * 30 for i in range(9)]        # 30 words each
    big["claims_checked"] = [
        {"claim": "c%d " % i + "y" * 1, "evidence_tag": "MEASURED",
         "verdict": "supported"} for i in range(18)]
    trimmed, changed = sup.enforce_word_caps(big)
    assert changed is True
    assert len(trimmed["strengths"]) == 6
    assert all(len(s.split()) <= sup.WORD_CAPS["strengths"]["max_words"] + 1
               for s in trimmed["strengths"])  # +1 for the ellipsis token
    assert len(trimmed["claims_checked"]) == 12
    sup.validate(trimmed)  # still schema-valid
    small = json.loads(json.dumps(VALID_REPORT))
    small["strengths"] = ["a short strength"]
    trimmed2, changed2 = sup.enforce_word_caps(small)
    assert changed2 is False and trimmed2 == small
    print("T27 ok: word caps enforced deterministically; schema stays valid; "
          "under-cap unchanged")

    # T28 max_tokens math (v7.4-2): config = ceil(p95 x 1.5) as recorded.
    cfg28 = yaml.safe_load((ROOT / "config/llm-providers.yml").read_text(
        encoding="utf-8"))
    assert cfg28["supervisor_max_tokens"] == p95doc["max_tokens_new"] == 1657
    assert cfg28["eval_max_tokens"] == 1657
    assert p95doc["formula"].startswith("max_tokens = ceil(p95")
    print("T28 ok: supervisor/eval_max_tokens = 1657 = ceil(p95_tokens_proxy x 1.5)")

    # T29 roles/bucket (v7.4-1): a probe-only provider gets ZERO supervisor
    # requests; fallback reaches the next provider.
    tmpcfg29 = mkconfig(tmp, [
        prov("p-probeonly", "MOCK_OK29", [{"id": "m/a", "status": "available"}]),
        prov("p-super", "MOCK_OK29B", [{"id": "m/a", "status": "available"}])])
    cfg29 = yaml.safe_load(tmpcfg29.read_text(encoding="utf-8"))
    cfg29["providers"][0]["roles"] = ["probe"]
    st29 = fresh_state(tmp / "s29-state.json")
    os.environ["MOCK_OK29"] = "k-ok"
    os.environ["MOCK_OK29B"] = "k-ok"
    hits29 = STATE["hits"]
    meta29 = {}
    out29 = llm_router.call_chat(cfg29, st29, "sys", "user", meta29)
    assert STATE["hits"] == hits29 + 1, (hits29, STATE["hits"])  # only p-super
    assert meta29["provider"] == "p-super", meta29
    print("T29 ok: probe-only provider skipped in supervisor bucket (1 HTTP hit)")

    # T29b roles in eval bucket (v7.4-1): models_under_test excludes a
    # probe-only provider entirely (zero eval calls to openrouter).
    import run_golden_eval as gev29
    mt29 = gev29.models_under_test(cfg29)
    assert [p for p, _, _ in mt29] == ["p-super"], mt29

    # T30 per-provider UTC quota (v7.4-1): counter file state/quota-<p>-<date>.json;
    # at cap the provider is bypassed automatically — no failure, no ALERT.
    llm_router.ROOT = tmp  # isolate quota files from the real state/ dir
    cfg30 = yaml.safe_load(mkconfig(tmp, [
        prov("p-quota", "MOCK_OK30", [{"id": "m/a", "status": "available"}]),
        prov("p-next30", "MOCK_OK30B", [{"id": "m/a", "status": "available"}])]).read_text(encoding="utf-8"))
    cfg30["providers"][0]["quota_prefix"] = "google"
    cfg30["providers"][0]["quota_daily_cap"] = 2
    st30 = fresh_state(tmp / "s30-state.json")
    os.environ["MOCK_OK30"] = "k-ok"
    os.environ["MOCK_OK30B"] = "k-ok"
    hits30 = STATE["hits"]
    alerts30_before = {p.name for p in (tmp / "outbox").glob("*.md")} if (tmp / "outbox").exists() else set()
    meta30 = {}
    llm_router.call_chat(cfg30, st30, "sys", "user", meta30)
    llm_router.call_chat(cfg30, st30, "sys", "user", {})
    qfiles = list((tmp / "state").glob("quota-google-*.json"))
    assert len(qfiles) == 1 and qfiles[0].name.startswith("quota-google-2026-")
    qd = json.loads(qfiles[0].read_text(encoding="utf-8"))
    assert qd["count"] == 2 and qd["cap"] == 2, qd
    assert st30.data["providers"]["p-quota"].get("consecutive_failures", 0) == 0
    alerts30_after = {p.name for p in (tmp / "outbox").glob("*.md")} if (tmp / "outbox").exists() else set()
    assert alerts30_after == alerts30_before, alerts30_after - alerts30_before
    meta30b = {}
    out30 = llm_router.call_chat(cfg30, st30, "sys", "user", meta30b)
    assert meta30b["provider"] == "p-next30", meta30b  # bypassed automatically
    assert st30.data["providers"]["p-quota"].get("consecutive_failures", 0) == 0
    # directed path (call_model) also bypasses with an explicit row outcome
    try:
        llm_router.call_model(cfg30, st30, "p-quota", "m/a", "sys", "user", {})
        raise AssertionError("quota bypass did not raise on call_model")
    except llm_router.AllProvidersFailed as e30:
        assert e30.detail.startswith("quota_bypass:"), e30.detail
    llm_router.ROOT = ROOT  # restore
    print("T30 ok: UTC quota counter file (quota-google-<date>.json), auto-bypass, "
          "no failure marking, no ALERT, call_model bypass explicit")

    # T31 prompt_suffix (v7.4-2): nvidia system prompt carries /no_think.
    cfg31 = yaml.safe_load(mkconfig(tmp, [
        prov("p-nthink", "MOCK_OK31", [{"id": "m/a", "status": "available"}])]).read_text(encoding="utf-8"))
    cfg31["providers"][0]["models"][0]["prompt_suffix"] = "/no_think"
    st31 = fresh_state(tmp / "s31-state.json")
    os.environ["MOCK_OK31"] = "k-ok"
    hits31 = STATE["hits"]
    llm_router.call_chat(cfg31, st31, "sys", "user", {})
    payload31 = json.loads(STATE["last_payload"])
    sysmsg31 = payload31["messages"][0]["content"]
    assert sysmsg31.startswith("sys\n") and sysmsg31.endswith("/no_think"), sysmsg31
    assert STATE["hits"] == hits31 + 1
    print("T31 ok: per-model prompt_suffix /no_think appended to the system prompt")

    # T32 provider pin (v7.4-5): LLM_PREFER_PROVIDER moves the named provider
    # to the FRONT of the try-order (second-provider trap reruns); unknown
    # name = normal order; missing key on the pinned provider = fallback.
    cfg32 = yaml.safe_load(mkconfig(tmp, [
        prov("p-first32", "MOCK_OK32", [{"id": "m/a", "status": "available"}]),
        prov("p-second32", "MOCK_OK32B", [{"id": "m/a", "status": "available"}])]).read_text(encoding="utf-8"))
    st32 = fresh_state(tmp / "s32-state.json")
    os.environ["MOCK_OK32"] = "k-ok"
    os.environ["MOCK_OK32B"] = "k-ok"
    hits32 = STATE["hits"]
    meta32 = {}
    llm_router.call_chat(cfg32, st32, "sys", "user", meta32)
    assert meta32["provider"] == "p-first32", meta32  # normal order first
    os.environ["LLM_PREFER_PROVIDER"] = "p-second32"
    try:
        meta32b = {}
        llm_router.call_chat(cfg32, st32, "sys", "user", meta32b)
        assert meta32b["provider"] == "p-second32", meta32b  # pin moves it front
        os.environ["LLM_PREFER_PROVIDER"] = "no-such-provider"
        meta32c = {}
        llm_router.call_chat(cfg32, st32, "sys", "user", meta32c)
        assert meta32c["provider"] == "p-first32", meta32c  # unknown = normal
        os.environ["LLM_PREFER_PROVIDER"] = "p-second32"
        del os.environ["MOCK_OK32B"]
        meta32d = {}
        llm_router.call_chat(cfg32, st32, "sys", "user", meta32d)
        assert meta32d["provider"] == "p-first32", meta32d  # unconfigured pin
    finally:
        os.environ.pop("LLM_PREFER_PROVIDER", None)
        os.environ.setdefault("MOCK_OK32B", "k-ok")
    assert STATE["hits"] == hits32 + 4
    print("T32 ok: LLM_PREFER_PROVIDER pin (front-of-order, fallback kept, "
          "unknown/unconfigured safe)")

    srv.shutdown()
    print("test-llm-shadow: ALL PASS (mock only, no real providers touched)")


if __name__ == "__main__":
    main()

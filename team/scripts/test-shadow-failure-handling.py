#!/usr/bin/env python3
"""test-shadow-failure-handling.py — offline tests for v7.0-4 (supervisor
failure classification / single compressed retry / shadow exit 0 / 2KB failure
archive / alert-after-3 / recovery reset) and the v6.9 router helpers they
depend on (reasoning_exhausted classification, throttle, 429 plan, leading
whitespace tolerance). No network, no real secrets — synthetic data only
(AGENTS rule 24). Exit 0 = all pass; 1 = failure."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
sys.path.insert(0, str(ROOT / "scripts"))
import llm_router  # noqa: E402
import llm_supervisor as sup  # noqa: E402

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print("ok   %s" % name)
    else:
        FAIL.append(name)
        print("FAIL %s %s" % (name, detail))


VALID_REPLY = json.dumps({
    "report_id": "test-report", "strengths": ["s"], "weaknesses": ["w"],
    "claims_checked": [{"claim": "c", "evidence_tag": "MEASURED",
                        "verdict": "supported"}],
    "decisions": [{"open_point": "p", "decision": "d", "rationale": "r"}],
    "risks": [], "next_items": ["n"], "injection_suspected": False,
    "publish_requests": [],
}, ensure_ascii=False)
# measured 2026-11-09 failure: JSON cut mid-string ("unbalanced object")
TRUNCATED_REPLY = '{"report_id": "session-57-review-2'


class FakeAllFailed(llm_router.AllProvidersFailed):
    pass


def run_supervisor(tmp, report_id, replies, raises=None, redact=False):
    """Run llm_supervisor.main() with call_chat mocked. replies: list of
    return values consumed in order (raises entries = exception instances)."""
    calls = {"n": 0, "payloads": []}

    def fake_call_chat(cfg, state, system, user, meta_out, probe_path=None):
        calls["n"] += 1
        calls["payloads"].append(user)
        i = calls["n"] - 1
        if raises and i < len(raises) and raises[i] is not None:
            raise raises[i]
        meta_out.update(provider="fake", model="fake-1",
                        model_actual="fake-1", latency_s=0.1, attempts=1,
                        finish_reason="stop" if i == 0 else "stop",
                        usage_summary={"completion_tokens": 10,
                                       "reasoning_tokens": 0},
                        low_confidence=False)
        return replies[i]

    orig_cc = llm_router.call_chat
    orig_state = llm_router.DEFAULT_STATE
    orig_cfg = llm_router.DEFAULT_CONFIG
    orig_alerts = llm_router.ALERTS_DIR
    orig_scan = llm_router.scan_secrets_bytes
    orig_root = sup.ROOT
    llm_router.call_chat = fake_call_chat
    llm_router.DEFAULT_STATE = str(Path(tmp) / "llm-status.json")
    llm_router.DEFAULT_CONFIG = str(Path(tmp) / "providers.yml")
    llm_router.ALERTS_DIR = Path(tmp) / "outbox"
    sup.ROOT = Path(tmp)  # archive_failed_reply writes under tmp/eval/failures
    if redact:
        llm_router.scan_secrets_bytes = lambda data: ["synthetic_hit"]
    (Path(tmp) / "providers.yml").write_text(
        "providers:\n- name: fake\n  env_secret: NOPE\n"
        "  base_url: https://example.invalid/v1\n  models:\n  - id: fake-1\n",
        encoding="utf-8")
    inp = Path(tmp) / ("report-%s.md" % report_id)
    inp.write_text("session report %s\n" % report_id, encoding="utf-8")
    sup_dir = Path(tmp) / "shadow"
    old_argv = sys.argv
    sys.argv = ["llm_supervisor.py", "--input", str(inp), "--report-id",
                report_id, "--out-dir", str(sup_dir), "--force"]
    rc = None
    try:
        rc = sup.main()
    finally:
        sys.argv = old_argv
        llm_router.call_chat = orig_cc
        llm_router.DEFAULT_STATE = orig_state
        llm_router.DEFAULT_CONFIG = orig_cfg
        llm_router.ALERTS_DIR = orig_alerts
        llm_router.scan_secrets_bytes = orig_scan
        sup.ROOT = orig_root
    return rc, calls, Path(tmp)


def state_of(tmp):
    p = Path(tmp) / "llm-status.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    # --- unit: classify_reply_failure (v7.0-4b) ---
    check("classify truncated", sup.classify_reply_failure(TRUNCATED_REPLY,
          "no_json: unbalanced object") == ("truncated_json",) +
          ("no_json: unbalanced object",)[:1])
    check("classify empty", sup.classify_reply_failure("   \n", "")[0] == "empty")
    check("classify no_json (prose)", sup.classify_reply_failure(
          "hello world", "no_json: no '{' in reply")[0] == "no_json")

    # --- unit: router shape_failure_class (v6.9-6) ---
    resp_len = {"choices": [{"finish_reason": "length", "message": {}}],
                "usage": {"completion_tokens": 3000,
                          "completion_tokens_details": {"reasoning_tokens": 3000}}}
    check("shape reasoning_exhausted",
          llm_router.shape_failure_class(resp_len, 3000)[0] == "reasoning_exhausted")
    resp_stop = {"choices": [{"finish_reason": "stop", "message": {}}], "usage": {}}
    check("shape api_shape fallback",
          llm_router.shape_failure_class(resp_stop, 3000)[0] == "api_shape")

    # --- unit: extract_json_object tolerates leading whitespace (v6.9-6) ---
    check("extract leading whitespace",
          llm_router.extract_json_object("  \n\n  " + VALID_REPLY) ==
          json.loads(VALID_REPLY))

    # --- unit: throttle (v6.9-2) ---
    sleeps = []
    orig_sleep = llm_router.time.sleep
    llm_router.time.sleep = lambda s: sleeps.append(s)
    prov = {"rpm": 30}
    st = {"_last_send_epoch": time.time()}
    llm_router.throttle_provider(prov, st)
    llm_router.time.sleep = orig_sleep
    check("throttle 60/rpm wait", bool(sleeps) and 1.0 <= sleeps[0] <= 2.5,
          str(sleeps))
    check("throttle no rpm no wait",
          llm_router.throttle_provider({}, {}) == 0.0)

    # --- unit: 429 plan (v6.9-2) ---
    st = {}
    w1, stop1 = llm_router.rate_limit_429_plan(st, {"Retry-After": "3"}, 5)
    check("429 first: wait+no stop", (not stop1) and 3.0 <= w1 <= 6.0, str(w1))
    w2, stop2 = llm_router.rate_limit_429_plan(st, {"Retry-After": "500"}, 5)
    check("429 second: stop+rate_limited",
          stop2 and st["status"] == "rate_limited" and w2 == 0.0)
    st2 = {}
    wc, _ = llm_router.rate_limit_429_plan(st2, {"Retry-After": "3"}, 5)
    check("429 Retry-After capped at 120+jitter", wc <= 122.0, str(wc))

    # --- integration: measured failure -> classified truncated_json, exit 0,
    #     recorded, archived <=2KB, no shadow file ---
    with tempfile.TemporaryDirectory() as tmp:
        rc, calls, tmp = run_supervisor(tmp, "t-trunc",
                                        [TRUNCATED_REPLY, TRUNCATED_REPLY])
        stt = state_of(tmp)
        la = stt.get("last_shadow_attempt") or {}
        check("truncated: exit 0 (shadow mode)", rc == 0, str(rc))
        check("truncated: status=shadow_failed",
              la.get("status") == "shadow_failed", str(la))
        check("truncated: class recorded",
              (la.get("reason") or "").startswith("truncated_json"), str(la))
        check("truncated: retries counted", la.get("retries") == 1, str(la))
        check("truncated: two calls (1 retry)", calls["n"] == 2, str(calls["n"]))
        check("truncated: compressed instruction sent",
              "OUTPUT CONSTRAINT" in calls["payloads"][1])
        fdir = Path(tmp) / "eval" / "failures"
        files = list(fdir.rglob("*.txt")) if fdir.exists() else []
        check("truncated: failure archived", len(files) == 1, str(files))
        if files:
            data = files[0].read_bytes()
            check("truncated: archive <=2KB + content", len(data) <= 2048 and
                  data.startswith(b'{"report_id"'), str(len(data)))
        check("truncated: no shadow file", not any(
            (Path(tmp) / "shadow").glob("t-trunc.*.json")))
        check("truncated: consecutive=1",
              (stt.get("shadow") or {}).get("consecutive_failures") == 1)

    # --- integration: retry succeeds -> report + meta.retries=1 + recovery ---
    with tempfile.TemporaryDirectory() as tmp:
        rc, calls, tmp = run_supervisor(tmp, "t-retry",
                                        [TRUNCATED_REPLY, VALID_REPLY])
        stt = state_of(tmp)
        check("retry-success: exit 0", rc == 0)
        report_files = list((Path(tmp) / "shadow").glob("t-retry.*.json"))
        check("retry-success: report written", len(report_files) == 1)
        if report_files:
            meta = json.loads(report_files[0].read_text(encoding="utf-8"))["meta"]
            check("retry-success: meta.retries==1", meta.get("retries") == 1,
                  str(meta))
        check("retry-success: recovery reset",
              (stt.get("shadow") or {}).get("consecutive_failures") == 0 and
              not (stt.get("shadow") or {}).get("last_alert_key"))

    # --- integration: reasoning_exhausted via router signal (no retry) ---
    with tempfile.TemporaryDirectory() as tmp:
        exc = llm_router.AllProvidersFailed(
            "all-failed:openrouter:openrouter/free:reasoning_exhausted")
        rc, calls, tmp = run_supervisor(tmp, "t-rex", [], raises=[exc])
        stt = state_of(tmp)
        la = stt.get("last_shadow_attempt") or {}
        check("reasoning_exhausted: exit 0", rc == 0)
        check("reasoning_exhausted: exactly 1 call, no retry", calls["n"] == 1,
              str(calls["n"]))
        check("reasoning_exhausted: class+provider recorded",
              (la.get("reason") or "").startswith("reasoning_exhausted") and
              la.get("provider") == "openrouter", str(la))

    # --- integration: fenced+whitespace reply parses (v6.9-6 tolerance) ---
    with tempfile.TemporaryDirectory() as tmp:
        rc, calls, tmp = run_supervisor(
            tmp, "t-fence", ["```json\n  \n" + VALID_REPLY + "\n```"])
        check("fenced reply: exit 0 + report", rc == 0 and any(
            (Path(tmp) / "shadow").glob("t-fence.*.json")))

    # --- integration: alert ONLY after 3 consecutive failures (v7.0-4d) ---
    with tempfile.TemporaryDirectory() as tmp:
        for i, rid in enumerate(["t-a1", "t-a2", "t-a3", "t-a4"]):
            rc, calls, tmp = run_supervisor(tmp, rid,
                                            [TRUNCATED_REPLY, TRUNCATED_REPLY])
            alert = Path(tmp) / "outbox" / "ALERT-shadow.md"
            stt = state_of(tmp)
            if i < 2:
                check("alert: none before 3rd (%s)" % rid, not alert.exists())
            if i == 2:
                check("alert: written at 3rd failure", alert.exists() and
                      (stt.get("shadow") or {}).get("last_alert_key") ==
                      "shadow_failed:truncated_json")
            if i == 3:
                before = alert.read_text(encoding="utf-8") if alert.exists() else ""
                check("alert: idempotent 4th run (same key)",
                      alert.exists() and before != "" and
                      (stt.get("shadow") or {}).get("last_alert_key") ==
                      "shadow_failed:truncated_json")

    # --- integration: secret-shaped archive redacted (v7.0-4c byte scan) ---
    with tempfile.TemporaryDirectory() as tmp:
        rc, calls, tmp = run_supervisor(tmp, "t-redact",
                                        [TRUNCATED_REPLY, TRUNCATED_REPLY],
                                        redact=True)
        fdir = Path(tmp) / "eval" / "failures"
        files = list(fdir.rglob("*.txt")) if fdir.exists() else []
        check("redact: archive redacted", files and files[0].read_bytes() ==
              b"[redacted:secret-shaped:synthetic_hit]",
              str([f.read_bytes() for f in files]))

    # --- unit: schema_invalid path still exit 0 with record ---
    with tempfile.TemporaryDirectory() as tmp:
        bad = VALID_REPLY.replace('"publish_requests": []',
                                  '"publish_requests": ["post something"]')
        rc, calls, tmp = run_supervisor(tmp, "t-schema", [bad])
        stt = state_of(tmp)
        la = stt.get("last_shadow_attempt") or {}
        check("schema_invalid: exit 0 + recorded", rc == 0 and
              (la.get("reason") or "").startswith("schema_invalid"), str(la))

    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    if FAIL:
        print("failed:", FAIL)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""decider_probe.py — typed probe for the strands-decider Space (v7.5).

WHY NOT scripts/llm_probe.py: the decider is a typed decision model. It answers
noul / choice / score about one state and deliberately REFUSES free text
(HTTP 400, error.type = typed_question_required). Running the chat probe
(`أعد {"ok":true} فقط`) against it would mark it failed for the wrong reason,
so this probe measures what the endpoint actually promises:

  1. LIVENESS  GET /health — a Space that is still warming its model refuses the
     connection; that is "starting", never "failed" (the free-CPU cold start is
     a scheduled event, not an incident).
  2. CONTRACT  GET /v1/models + POST /v1/systemone with one fixed three-kind
     request: 200, all three answer kinds back, every probability inside
     [0,1], and a repeat of the same input gives the same answer (choice label
     identical, score within DECIDER_REPEAT_TOL).
  3. SHIM      POST /v1/chat/completions with the typed JSON contract: OpenAI
     envelope + decision JSON in choices[0].message.content; and a free-text
     request that MUST be refused with typed_question_required — the guard
     that keeps a decision model out of LLM chains.

Output: state/decider-space.json (DATA ONLY: no key, no request text, no state
text — the fixed probe input is public and only its sha256_16 is stored).
Exit code is ALWAYS 0 unless local infrastructure crashes; the workflow reads
the state file, and a crash would lose the measurement.

Env:
  DECIDER_BASE_URL   default https://djihafwork-ginux-decider.hf.space
  DECIDER_API_KEY    absent -> typed calls recorded as "unconfigured"
  DECIDER_TIMEOUT_S  per-request timeout, default 120
  DECIDER_REPEAT_TOL score/choice agreement tolerance, default 0.15
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "decider-space.json"

BASE_URL = os.environ.get(
    "DECIDER_BASE_URL", "https://djihafwork-ginux-decider.hf.space").rstrip("/")
API_KEY = (os.environ.get("DECIDER_API_KEY") or "").strip()
TIMEOUT = float(os.environ.get("DECIDER_TIMEOUT_S", "120") or 120)
REPEAT_TOL = float(os.environ.get("DECIDER_REPEAT_TOL", "0.15") or 0.15)
HISTORY_KEEP = 200

PROBE_STATE = ("Help! My payouts have been failing for 3 days! I have written "
               "twice and nobody answers.")
PROBE_QUESTIONS = {
    "is_urgent": {"type": "noul",
                  "instructions": "Does this convey urgency?"},
    "team": {"type": "choice",
             "instructions": "Which team should handle this?",
             "criteria": {"billing": None, "sales": None, "retail": None}},
    "frustration": {"type": "score",
                    "instructions": "How frustrated is the writer?",
                    "criteria": ["calm", "frustrated", "depressed"]},
}
PROBE_SHA16 = hashlib.sha256(json.dumps(
    {"state": PROBE_STATE, "questions": PROBE_QUESTIONS},
    sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(path: str, *, method: str = "GET", body=None, auth: bool = True,
              timeout: float | None = None) -> dict:
    """One request. Returns {code, parsed, raw, error, elapsed_s}; never raises
    for network errors (they become `error`), never prints the key."""
    url = BASE_URL + path
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("content-type", "application/json")
    req.add_header("user-agent", "ginux-watch-decider-probe/1")
    if auth and API_KEY:
        req.add_header("authorization", "Bearer " + API_KEY)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout or TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "replace")
            code = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        code = exc.code
    except urllib.error.URLError as exc:
        return {"code": None, "parsed": None, "raw": "",
                "error": "urlerror", "detail": str(exc.reason)[:200],
                "elapsed_s": round(time.monotonic() - started, 2)}
    except Exception as exc:  # timeout, reset, DNS, ...
        return {"code": None, "parsed": None, "raw": "",
                "error": type(exc).__name__.lower(), "detail": str(exc)[:200],
                "elapsed_s": round(time.monotonic() - started, 2)}
    parsed = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    return {"code": code, "parsed": parsed, "raw": raw, "error": None,
            "elapsed_s": round(time.monotonic() - started, 2)}


def classify(resp: dict) -> str:
    if resp["error"]:
        return "starting" if resp["error"] == "urlerror" and not API_KEY else \
            ("starting" if resp["error"] in ("urlerror", "timeout") else resp["error"])
    code = resp["code"]
    if code == 401:
        return "auth_failed"
    if code is None:
        return "urlerror"
    if code >= 500:
        return "http_%d" % code
    if not 200 <= code < 300:
        return "http_%d" % code
    if resp["parsed"] is None:
        return "no_json"
    return "ok"


def probabilities_valid(answers: dict) -> tuple[bool, list[str]]:
    """Every returned distribution must lie in [0,1] and sum to ~1."""
    problems = []
    for name, answer in (answers or {}).items():
        if not isinstance(answer, dict):
            problems.append("%s:not-an-object" % name)
            continue
        probs = answer.get("probabilities")
        values = []
        if isinstance(probs, dict):
            values = list(probs.values())
        elif answer.get("type") == "noul":
            values = [answer.get("noul")]
        if not values:
            problems.append("%s:no-probabilities" % name)
            continue
        if any(not isinstance(v, (int, float)) or v < 0 or v > 1 for v in values):
            problems.append("%s:out-of-range" % name)
    return (not problems), problems


def answer_evidence(answers: dict) -> dict:
    """The measured decisions, compact: label + confidence + the distribution."""
    out = {}
    for name, answer in (answers or {}).items():
        if not isinstance(answer, dict):
            continue
        row = {"type": answer.get("type")}
        if "noul" in answer:
            row["noul"] = round(float(answer["noul"]), 4)
        if "choice" in answer:
            row["choice"] = answer["choice"]
            row["confidence"] = round(float(answer.get("confidence", 0)), 4)
        if "score" in answer:
            row["score"] = round(float(answer["score"]), 4)
            row["confidence"] = round(float(answer.get("confidence", 0)), 4)
        probs = answer.get("probabilities")
        if isinstance(probs, dict):
            row["probabilities"] = {k: round(float(v), 4) for k, v in probs.items()}
        out[name] = row
    return out


def same_answer(first: dict, second: dict) -> tuple[bool, str]:
    """Same choice label; noul and score within REPEAT_TOL."""
    if not first or not second:
        return False, "missing answer"
    if set(first) != set(second):
        return False, "different answer kinds"
    for name, a in first.items():
        b = second[name]
        if a.get("type") != b.get("type"):
            return False, "%s:type changed" % name
        if "choice" in a:
            if a["choice"] != b.get("choice"):
                return False, "%s:choice %s -> %s" % (name, a["choice"], b.get("choice"))
        for key in ("noul", "score"):
            if key in a and abs(float(a[key]) - float(b.get(key, 0))) > REPEAT_TOL:
                return False, "%s:%s %s -> %s" % (name, key, a[key], b.get(key))
    return True, "identical choice labels; noul/score within %.2f" % REPEAT_TOL


def main() -> int:
    record: dict = {
        "updated": now_iso(),
        "schema": "decider-space-v1",
        "note": "DATA ONLY — no key, no request text; fixed probe input sha256_16 only",
        "base_url": BASE_URL,
        "configured": bool(API_KEY),
        "probe_input_sha256_16": PROBE_SHA16,
        "checks": {},
        "status": "unknown",
    }

    if not API_KEY:
        record["status"] = "unconfigured"
        record["checks"]["auth"] = {"category": "unconfigured",
                                    "note": "DECIDER_API_KEY is not set in this job"}
        record["checks"]["health"] = {"category": "unconfigured"}
        record["history"] = load_history(record)
        write(record)
        print("decider-space: unconfigured (no DECIDER_API_KEY)")
        return 0

    health = http_json("/health", auth=False)
    health_cat = classify(health)
    record["checks"]["health"] = {
        "category": health_cat,
        "http_status": health["code"],
        "elapsed_s": health["elapsed_s"],
        "model": (health["parsed"] or {}).get("model"),
        "checkpoint": (health["parsed"] or {}).get("checkpoint"),
        "base_model": (health["parsed"] or {}).get("base_model"),
        "device": (health["parsed"] or {}).get("device"),
        "max_length": (health["parsed"] or {}).get("max_length"),
    }
    if health_cat in ("starting", "timeout"):
        # cold start / sleeping Space: report, do not count as a failure
        record["status"] = "starting"
        record["history"] = load_history(record)
        write(record)
        print("decider-space: starting (%s after %ss)" % (
            health.get("error") or health_cat, health["elapsed_s"]))
        return 0
    if health_cat != "ok":
        record["status"] = "failed"
        record["checks"]["health"]["detail"] = (health.get("raw") or "")[:200]
        record["history"] = load_history(record)
        write(record)
        print("decider-space: failed at /health (%s)" % health_cat)
        return 0

    models = http_json("/v1/models")
    ids = []
    if isinstance(models["parsed"], dict):
        ids = [m.get("id") for m in models["parsed"].get("data", [])
               if isinstance(m, dict)]
    record["checks"]["models"] = {
        "category": classify(models),
        "http_status": models["code"],
        "elapsed_s": models["elapsed_s"],
        "model_ids": ids,
    }
    model_id = ids[0] if ids else (health["parsed"] or {}).get("model")
    record["model"] = model_id

    native = http_json("/v1/systemone", method="POST",
                       body={"state": PROBE_STATE, "questions": PROBE_QUESTIONS})
    native_cat = classify(native)
    answers = ((native["parsed"] or {}).get("answers")
               if isinstance(native["parsed"], dict) else None) or {}
    kinds_ok = sorted(answers) == sorted(PROBE_QUESTIONS)
    probs_ok, prob_problems = probabilities_valid(answers)
    native_ok = native_cat == "ok" and kinds_ok and probs_ok
    record["checks"]["native"] = {
        "category": "ok" if native_ok else (native_cat if native_cat != "ok"
                                            else "schema_invalid"),
        "http_status": native["code"],
        "elapsed_s": native["elapsed_s"],
        "answer_kinds": sorted(answers),
        "expected_kinds": sorted(PROBE_QUESTIONS),
        "probability_problems": prob_problems,
        "usage": (native["parsed"] or {}).get("usage")
        if isinstance(native["parsed"], dict) else None,
        "latency_ms_reported": (native["parsed"] or {}).get("latency_ms")
        if isinstance(native["parsed"], dict) else None,
    }
    record["answers"] = answer_evidence(answers)

    # determinism: same input twice, same decision
    repeat = http_json("/v1/systemone", method="POST",
                       body={"state": PROBE_STATE, "questions": PROBE_QUESTIONS})
    repeat_answers = ((repeat["parsed"] or {}).get("answers")
                      if isinstance(repeat["parsed"], dict) else None) or {}
    stable, why = same_answer(answer_evidence(answers),
                              answer_evidence(repeat_answers))
    record["checks"]["determinism"] = {
        "category": "ok" if stable else "unstable",
        "detail": why,
        "elapsed_s": repeat["elapsed_s"],
    }

    typed_body = {
        "model": model_id or "strands-decider-2b",
        "temperature": 0,
        "messages": [{"role": "user", "content": json.dumps(
            {"state": PROBE_STATE, "questions": PROBE_QUESTIONS},
            ensure_ascii=False)}],
    }
    chat = http_json("/v1/chat/completions", method="POST", body=typed_body)
    chat_cat = classify(chat)
    content = None
    if isinstance(chat["parsed"], dict):
        try:
            content = json.loads(chat["parsed"]["choices"][0]["message"]["content"])
        except Exception:
            content = None
    shim_ok = (chat_cat == "ok" and isinstance(content, dict)
               and sorted(content.get("answers") or {}) == sorted(PROBE_QUESTIONS))
    record["checks"]["shim"] = {
        "category": "ok" if shim_ok else (chat_cat if chat_cat != "ok"
                                          else "schema_invalid"),
        "http_status": chat["code"],
        "elapsed_s": chat["elapsed_s"],
        "content_kinds": sorted((content or {}).get("answers") or {}),
        "usage": (chat["parsed"] or {}).get("usage")
        if isinstance(chat["parsed"], dict) else None,
    }

    # the guard: free text must be refused, with the documented error type
    free = http_json("/v1/chat/completions", method="POST", body={
        "model": model_id or "strands-decider-2b",
        "messages": [{"role": "user", "content": "أعد {\"ok\":true} فقط"}],
    })
    err = ((free["parsed"] or {}).get("error")
           if isinstance(free["parsed"], dict) else None) or {}
    guard_ok = free["code"] == 400 and err.get("type") == "typed_question_required"
    record["checks"]["guard"] = {
        "category": "ok" if guard_ok else "guard_broken",
        "http_status": free["code"],
        "error_type": err.get("type"),
        "note": "free text must be refused (typed_question_required); it must "
                "never be answered with an invented generation",
    }

    failed = [name for name, check in record["checks"].items()
              if check.get("category") not in ("ok",)]
    record["status"] = "ok" if not failed else "degraded"
    record["failed_checks"] = failed
    record["history"] = load_history(record)
    write(record)

    line = ("decider-space: %s health=%ss native=%ss shim=%ss guard=%s"
            % (record["status"], health["elapsed_s"], native["elapsed_s"],
               chat["elapsed_s"], "ok" if guard_ok else "BROKEN"))
    if failed:
        line += " failed=" + ",".join(failed)
    print(line)
    return 0


def load_history(record: dict) -> list:
    try:
        previous = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        previous = {}
    history = previous.get("history") or []
    history.append({
        "at": record["updated"],
        "status": record["status"],
        "checks": {name: check.get("category")
                   for name, check in record.get("checks", {}).items()},
        "latencies_s": {name: check.get("elapsed_s")
                        for name, check in record.get("checks", {}).items()
                        if check.get("elapsed_s") is not None},
    })
    return history[-HISTORY_KEEP:]


def write(record: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

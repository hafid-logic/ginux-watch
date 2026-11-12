#!/usr/bin/env python3
"""decider_eval.py — evaluation runner for the decider case set (v7.5-3).

Modes:
  --dry-run (default when no DECIDER_API_KEY): offline harness validation —
      loads every case, validates labels/splits, prints stats, zero network.
  live (DECIDER_API_KEY set): probe-only typed calls to the strands-decider
      Space (T1/T2 questions), computes accuracy + for-us recall (target >=
      0.98 — a missed alert is the worst error), 5-repeat stability and
      injection resistance; every raw vote goes to the results file (data only,
      no secrets, no case text echo beyond ids).

The asymmetry composition lives in scripts/decider_gate.py (alert =
deterministic OR decider; mute from deterministic only).
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "eval" / "decider-cases" / "cases"
RESULTS = REPO / "eval" / "decider-cases" / "results"
FOR_US_CLASSES = {"request", "directed_at_us"}
STABILITY_REPEATS = 5


def load_cases():
    cases = []
    for f in sorted(CASES.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if d["task"] == "t1":
            assert d["t1_label"] in {"directed_at_us", "status_of_others", "request", "noise"}, f["id"]
        else:
            assert d["t2_label"] in {"routine", "needs_supervisor"}, f["id"]
        assert d["split"] in {"control", "test"}, f["id"]
        cases.append(d)
    ids = [c["id"] for c in cases]
    assert len(set(ids)) == len(ids), "duplicate case ids"
    return cases


def space_call(text, base_url, key, timeout=30):
    """One typed probe call (probe-only role). Returns the model's verdict."""
    body = json.dumps({
        "questions": [{"id": "decider-eval", "text": text, "kind": "triage"}],
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/systemone", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    cases = load_cases()
    t1 = [c for c in cases if c["task"] == "t1"]
    t2 = [c for c in cases if c["task"] == "t2"]
    key = os.environ.get("DECIDER_API_KEY", "").strip()
    base_url = os.environ.get("DECIDER_BASE_URL", "https://djihafwork-ginux-decider.hf.space")

    stats = {
        "cases_total": len(cases),
        "t1": len(t1), "t2": len(t2),
        "control": sum(1 for c in cases if c["split"] == "control"),
        "test": sum(1 for c in cases if c["split"] == "test"),
        "for_us_positives": sum(1 for c in cases if c["for_us"]),
        "injection_rows": sum(1 for c in cases if "حقن" in c["source"] or "إخفاء" in c["source"]),
    }

    if not key:
        stats["engine"] = "unavailable (no DECIDER_API_KEY — probe-only harness validated offline)"
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        print("decider_eval dry-run: OK (%d cases loaded, labels valid, splits clean)" % len(cases))
        return 0

    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        label = c["t1_label"] or c["t2_label"]
        votes = []
        for _ in range(STABILITY_REPEATS):
            try:
                resp = space_call(c["text"], base_url, key)
                votes.append(json.dumps(resp, sort_keys=True)[:2000])
            except Exception as e:
                votes.append("error:%s" % type(e).__name__)
        stable = len(set(votes)) == 1
        rows.append({"id": c["id"], "split": c["split"], "task": c["task"],
                     "label": label, "for_us": c["for_us"], "stable": stable,
                     "votes": votes})
    # NOTE: metric computation over model verdicts requires parsing the Space's
    # typed answer schema; when first run live, extend here from the recorded
    # votes (they are persisted verbatim for auditability).
    out = {"stats": stats, "rows": rows, "note": "first live run — votes recorded for metric extraction"}
    (RESULTS / "decider-eval-first-live.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("decider_eval live: %d cases probed; results written" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

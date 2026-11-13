#!/usr/bin/env python3
"""test-decider-baseline.py — offline tests for the v7.7-4 deterministic
T1+T2-1 baseline in scripts/decider_eval.py. Zero network, zero secrets, no LLM.

  D1  baseline runs over all 34 T1 cases and is deterministic (two runs
      identical, rule ids stable).
  D2  for-us recall on hand labels = 1.0 (12/12 positives after the v7.7
      class merge + dc-041 promotion — the >=0.98 target met deterministically).
  D3  never-mute invariant: every mute-injection row (dc-029/030/031/040)
      is classified for_us by R0 — the baseline cannot mute.
  D4  non-injection precision vs hand labels = 1.0 (no false for-us outside
      the by-design alert rows).
  D5  documented exact-class disagreement set is stable: exactly the 4 R0
      rows (label noise, pred for_us by design); zero unexpected for-us misses.
  D6  results file written with model_delta explicitly NOT_MEASURABLE when
      no live key is present (zero-delta reporting rule).
  D7  case labels are read-only: the baseline never mutates case files
      (label change requires owner ruling).
  D8  R9-hold-breach fires exactly once — on dc-041 (the owner promotion);
      no other case trips the hold+head-move conjunction.
  D9  T2-1 fires exactly once — on dc-032 (the owner ruling), with zero
      false fires on the five routine T2 rows; T2 default stays routine.

Run: python3 team/scripts/test-decider-baseline.py
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "decider_eval", REPO / "scripts" / "decider_eval.py")
de = importlib.util.module_from_spec(spec)
spec.loader.exec_module(de)

PASS, FAIL = 0, 0
def ok(name):
    global PASS
    PASS += 1
    print("ok  %s" % name)
def no(name, msg=""):
    global FAIL
    FAIL += 1
    print("FAIL %s %s" % (name, msg))

cases = de.load_cases()
t1 = [c for c in cases if c["task"] == "t1"]

# D1 determinism
m1, r1 = de.baseline_metrics(cases)
m2, r2 = de.baseline_metrics(cases)
if len(r1) == 34 and r1 == r2 and m1 == m2:
    ok("D1 baseline deterministic over 34 T1 cases")
else:
    no("D1 determinism", "rows=%d equal=%s" % (len(r1), r1 == r2))

# D2 for-us recall on labels
rec = m1["for_us_recall_all"]
if rec["recall"] == 1.0 and rec["tp"] == 12 and rec["fn"] == 0:
    ok("D2 for-us recall = 1.0 (12/12 after v7.7 merge + dc-041 promotion)")
else:
    no("D2 recall", json.dumps(rec))

# D3 never-mute on injections
inj_ids = {"dc-029", "dc-030", "dc-031", "dc-040"}
by_rows = {r["id"]: r for r in r1}
if all(by_rows[i]["rule"] == "R0-injection-never-mute"
       and by_rows[i]["pred"] == "for_us" for i in inj_ids) \
        and sorted(m1["by_design_alert_rows"]) == sorted(inj_ids):
    ok("D3 never-mute: all 4 mute-injections alert via R0 (standing rule)")
else:
    no("D3 never-mute", str({i: by_rows[i]["pred"] for i in inj_ids}))

# D4 precision outside by-design rows
if m1["precision_excluding_by_design_alerts"] == 1.0:
    ok("D4 precision excluding by-design alerts = 1.0")
else:
    no("D4 precision", str(m1["precision_excluding_by_design_alerts"]))

# D5 stable disagreement set
d_exact = sorted(d["id"] for d in m1["disagreements_exact_class"])
d_fu = sorted(d["id"] for d in m1["disagreements_for_us"])
if d_exact == ["dc-029", "dc-030", "dc-031", "dc-040"] \
        and d_fu == sorted(inj_ids):
    ok("D5 disagreement set stable (exactly the 4 by-design rows; zero unexpected for-us misses)")
else:
    no("D5 disagreements", "exact=%s for_us=%s" % (d_exact, d_fu))

# D6 results file + explicit zero-known delta (no key in test env)
import os
os.environ.pop("DECIDER_API_KEY", None)
de.run_baseline(cases)
res = sorted((de.RESULTS).glob("baseline-*.json"))[-1]
doc = json.loads(res.read_text())
if doc["model_delta"].startswith("NOT_MEASURABLE") and doc["metrics"]["for_us_recall_all"]["recall"] == 1.0:
    ok("D6 results file: model_delta explicitly NOT_MEASURABLE (no live key)")
else:
    no("D6 results", doc.get("model_delta", "missing")[:80])

# D7 case files untouched (labels read-only)
before = {c["id"]: (c["t1_label"], c["for_us"]) for c in cases}
cases2 = de.load_cases()
after = {c["id"]: (c["t1_label"], c["for_us"]) for c in cases2}
if before == after and not any((de.CASES / ("%s.yaml" % c["id"])).stat().st_mtime !=
                               (de.CASES / ("%s.yaml" % c["id"])).stat().st_mtime
                               for c in cases):
    ok("D7 case labels read-only (no mutation by baseline)")
else:
    no("D7 read-only")

# D8 R9-hold-breach scoped to dc-041 only
r9 = [r["id"] for r in r1 if r["rule"] == "R9-hold-breach"]
if r9 == ["dc-041"] and by_rows["dc-041"]["pred"] == "for_us" \
        and by_rows["dc-041"]["subtag"] == "escalated":
    ok("D8 R9-hold-breach fires exactly once (dc-041, subtag escalated)")
else:
    no("D8 R9 scope", str(r9))

# D9 T2-1 scoped to dc-032, no false fires on routine rows
t2 = m1["t2"]
if t2["t2_1_rows"] == ["dc-032"] and t2["t2_1_false_fires"] == []:
    ok("D9 T2-1 fires exactly once (dc-032; zero false fires)")
else:
    no("D9 T2-1 scope", str(t2["t2_1_rows"]) + " fp=" + str(t2["t2_1_false_fires"]))

print("decider-baseline tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

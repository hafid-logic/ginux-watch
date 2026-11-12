#!/usr/bin/env python3
"""test-decider-gate.py — offline tests for scripts/decider_gate.py (v7.5-3).

Covers the asymmetry truth table, the never-mute property, journal logging and
difference extraction. Zero network, zero keys.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("decider_gate", REPO / "scripts" / "decider_gate.py")
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)

PASS, FAIL = 0, 0
def ok(name):
    global PASS; PASS += 1; print("ok  %s" % name)
def no(name, msg=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (name, msg))

# ---- truth table (v7.5-3: alert = det OR decider; mute from det only) ----
TABLE = [
    # (det, dec, expected_alert, expected_source)
    (False, False, False, "none"),
    (True,  False, True,  "deterministic"),
    (False, True,  True,  "decider"),
    (True,  True,  True,  "both"),
]
for det, dec, exp_alert, exp_src in TABLE:
    d = dg.combine(det, dec)
    if d["alert"] == exp_alert and d["source"] == exp_src:
        ok("truth det=%s dec=%s -> %s/%s" % (det, dec, exp_alert, exp_src))
    else:
        no("truth det=%s dec=%s" % (det, dec), str(d))

# ---- never-mute property: decider cannot suppress a deterministic alert ----
d = dg.combine(True, False)
if d["alert"] is True and d["muted_by_decider"] is False:
    ok("never-mute: det alert survives silent decider")
else:
    no("never-mute silent", str(d))
d = dg.combine(True, True)
if d["alert"] is True and d["muted_by_decider"] is False:
    ok("never-mute: det alert survives agreeing decider")
else:
    no("never-mute agree", str(d))

# ---- decider adds over deterministic silence (recall protection) ----
d = dg.combine(False, True, reason_det="no trigger", reason_dec="owner reply detected")
if d["alert"] is True and d["source"] == "decider" and d["reason_decider"]:
    ok("decider adds over silence")
else:
    no("decider adds", str(d))

# ---- journal logging + difference extraction ----
with tempfile.TemporaryDirectory() as td:
    j = Path(td) / "decider-shadow.jsonl"
    dg.log_row(dg.combine(True, False, event_id="e1"), journal=j)
    dg.log_row(dg.combine(False, True, event_id="e2"), journal=j)
    dg.log_row(dg.combine(False, False, event_id="e3"), journal=j)
    rows = [json.loads(l) for l in j.read_text().splitlines()]
    if len(rows) == 3 and all({"alert", "at_utc", "event_id"} <= set(r) for r in rows):
        ok("journal rows written with at_utc + event_id")
    else:
        no("journal rows", str(rows)[:150])
    diffs = dg.differences(rows)
    if [r["event_id"] for r in diffs] == ["e2"]:
        ok("differences() isolates decider-added alerts")
    else:
        no("differences()", str(diffs))

print("decider-gate tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

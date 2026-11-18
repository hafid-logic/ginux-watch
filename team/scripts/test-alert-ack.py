#!/usr/bin/env python3
"""test-alert-ack.py — offline tests for alert-ack pure core + ledger (v8.4-C)."""
import importlib.util, sys, tempfile, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
def loadmod(name, p):
    s = importlib.util.spec_from_file_location(name, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
aa = loadmod("aa", REPO / "team/scripts/alert-ack.py")
led = loadmod("led", REPO / "scripts/action_ledger.py")
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
ok("K1 label ack") if aa.acknowledged([{"name": "Acknowledged"}], []) else no("K1")
ok("K2 owner ACK comment") if aa.acknowledged([], [{"user": {"login": "hafid-logic"}, "body": "ACK noted"}]) else no("K2")
ok("K3 owner Arabic ack") if aa.acknowledged([], [{"user": {"login": "hafid-logic"}, "body": "تم اقرار البند"}]) else no("K3")
ok("K4 non-owner ack ignored") if not aa.acknowledged([], [{"user": {"login": "random"}, "body": "ACK"}]) else no("K4")
ok("K5 no ack") if not aa.acknowledged([], [{"user": {"login": "hafid-logic"}, "body": "still looking"}]) else no("K5")
ok("K6 never reminded => due") if aa.reminder_due(None, "2026-11-18T12:00:00Z") else no("K6")
ok("K7 recent => not due") if not aa.reminder_due("2026-11-18T10:00:00Z", "2026-11-18T12:00:00Z") else no("K7")
ok("K8 old => due") if aa.reminder_due("2026-11-18T05:00:00Z", "2026-11-18T12:00:00Z") else no("K8")
tmp = tempfile.mktemp(suffix=".jsonl")
led.record({"action": "alert_reminder", "target": "5"}, tmp)
ok("K9 ledger already") if led.already("alert_reminder", "5", tmp) else no("K9")
ok("K10 ledger not-already") if not led.already("alert_reminder", "6", tmp) else no("K10")
os.unlink(tmp)
print("alert-ack tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

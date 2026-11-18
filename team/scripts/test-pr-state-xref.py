#!/usr/bin/env python3
"""test-pr-state-xref.py — offline tests (v8.3-ب). Zero network/secrets."""
import importlib.util, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("prx", REPO / "scripts/pr-state-xref.py")
prx = importlib.util.module_from_spec(spec); spec.loader.exec_module(prx)
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
M = {"our_open_prs": {"295": {}, "296": {}}}
ok("X1 both referenced") if prx.missing_prs(M, "#295 #296") == [] else no("X1")
ok("X2 missing 296") if prx.missing_prs(M, "#295 only") == ["296"] else no("X2")
ok("X3 pull/n form") if prx.missing_prs(M, "pull/295 pull/296") == [] else no("X3")
ok("X4 empty set") if prx.missing_prs({"our_open_prs": {}}, "x") == [] else no("X4")
ok("X5 absent key") if prx.missing_prs({}, "x") == [] else no("X5")
ok("X6 word boundary") if prx.missing_prs(M, "#2950 #296") == ["295"] else no("X6")
print("pr-state-xref tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

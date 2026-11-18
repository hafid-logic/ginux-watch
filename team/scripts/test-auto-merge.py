#!/usr/bin/env python3
"""test-auto-merge.py — offline tests for decide() (v8.4-B). Zero network/secrets."""
import importlib.util, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
spec = importlib.util.spec_from_file_location("am", REPO / "team/scripts/auto-merge.py")
am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
az = am.az
pol = az.load()
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
R = "hafid-logic/ginux-watch"
def PR(**kw):
    d = {"state": "open", "draft": False, "mergeable_state": "clean",
         "head": {"repo": {"full_name": R}}, "base": {"repo": {"full_name": R}}}
    d.update(kw); return d
ok("M1 clean allowlisted => auto") if am.decide(PR(), ["team/scripts/x.py"], "success", pol) == ("auto", "allowlist") else no("M1")
ok("M2 fork => skip") if am.decide(PR(head={"repo": {"full_name": "evil/fork"}}), ["team/x.py"], "success", pol)[0] == "skip" else no("M2")
ok("M3 draft => skip") if am.decide(PR(draft=True), ["team/x.py"], "success", pol)[0] == "skip" else no("M3")
ok("M4 ci failure => skip") if am.decide(PR(), ["team/x.py"], "failure", pol)[0] == "skip" else no("M4")
ok("M5 dirty => skip") if am.decide(PR(mergeable_state="dirty"), ["team/x.py"], "success", pol)[0] == "skip" else no("M5")
ok("M6 closed => skip") if am.decide(PR(state="closed"), ["team/x.py"], "success", pol)[0] == "skip" else no("M6")
ok("M7 guardrail file => needs-owner") if am.decide(PR(), ["config/authorization.yml"], "success", pol)[0] == "needs-owner" else no("M7")
ok("M8 outside allowlist => needs-owner") if am.decide(PR(), ["Makefile"], "success", pol)[0] == "needs-owner" else no("M8")
ok("M9 empty => needs-owner") if am.decide(PR(), [], "success", pol)[0] == "needs-owner" else no("M9")
ok("M10 self-protection auto-merge.py") if am.decide(PR(), ["team/scripts/auto-merge.py"], "success", pol)[0] == "needs-owner" else no("M10")
print("auto-merge tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

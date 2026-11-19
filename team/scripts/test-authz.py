#!/usr/bin/env python3
"""test-authz.py — offline tests for scripts/authz_check.py (v8.4). Zero network."""
import importlib.util, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("az", REPO / "scripts/authz_check.py")
az = importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
pol = az.load()
ok("A1 autonomous action") if az.classify("internal_pr_merge", pol) == "autonomous" else no("A1")
ok("A2 human action") if az.classify("upstream_mutation", pol) == "human" else no("A2")
ok("A3 unknown defaults human") if az.classify("launch_rockets", pol) == "human" else no("A3")
ok("A4 allowlisted files auto") if az.pr_files_decision(["team/scripts/x.py", "reports/r.md"], pol)[0] == "auto" else no("A4")
ok("A5 denylist overrides allowlist") if az.pr_files_decision(["scripts/authz_check.py"], pol)[0] == "needs-owner" else no("A5")
ok("A6 policy file denied") if az.pr_files_decision(["POLICY.md"], pol)[0] == "needs-owner" else no("A6")
ok("A7 outside allowlist") if az.pr_files_decision(["Cargo.toml"], pol)[0] == "needs-owner" else no("A7")
ok("A8 foreign workflow denied") if az.pr_files_decision([".github/workflows/fuzz.yml"], pol)[0] == "needs-owner" else no("A8")
ok("A9 ci workflow now denied (v8.7)") if az.pr_files_decision([".github/workflows/ci.yml"], pol)[0] == "needs-owner" else no("A9")
ok("A10 empty pr needs owner") if az.pr_files_decision([], pol)[0] == "needs-owner" else no("A10")
ok("A11 hooks denied") if az.pr_files_decision(["scripts/hooks/install-pre-commit.sh"], pol)[0] == "needs-owner" else no("A11")
ok("A12 automation self-protection") if az.pr_files_decision(["team/scripts/auto-merge.py"], pol)[0] == "needs-owner" else no("A12")
print("authz tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

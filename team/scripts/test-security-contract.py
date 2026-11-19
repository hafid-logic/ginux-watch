#!/usr/bin/env python3
"""test-security-contract.py — offline tests for the binding-contract gate (v8.6)."""
import importlib.util, shutil, sys, tempfile
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("sc", REPO / "scripts/security_contract_check.py")
sc = importlib.util.module_from_spec(s); s.loader.exec_module(sc)
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
FILES = ["docs/AGENT-SECURITY.md", "AGENTS.md", "config/authorization.yml", ".github/workflows/ci.yml"]
def mktree():
    t = Path(tempfile.mkdtemp())
    for f in FILES:
        d = t / f; d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / f, d)
    return t
ok("S1 real repo passes") if sc.check() == [] else no("S1", str(sc.check()))
t = mktree(); ok("S2 copied tree passes") if sc.check(t) == [] else no("S2", str(sc.check(t)))
t = mktree(); p = t / "docs/AGENT-SECURITY.md"; p.write_text(p.read_text().replace("EVERY agent", "some agents"))
ok("S3 weakened clause detected") if sc.check(t) else no("S3")
t = mktree(); p = t / "AGENTS.md"; p.write_text(p.read_text().replace("HDAE SECURITY CONTRACT", "X"))
ok("S4 missing AGENTS block detected") if sc.check(t) else no("S4")
t = mktree(); p = t / "config/authorization.yml"
p.write_text(p.read_text().replace("order: [device_flow,", "order: [short_lived_pat,"))
ok("S5 tier reorder detected") if sc.check(t) else no("S5")
t = mktree(); p = t / "config/authorization.yml"
p.write_text("\n".join(l for l in p.read_text().splitlines() if not l.strip().startswith("- gate_acceptance")))
ok("S6 human_required weakening detected") if sc.check(t) else no("S6")
t = mktree(); p = t / ".github/workflows/ci.yml"
p.write_text(p.read_text().replace("security_contract_check.py", "true.py"))
ok("S7 ci gate removal detected") if sc.check(t) else no("S7")
print("security-contract tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

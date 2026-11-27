#!/usr/bin/env python3
"""dedup — the anti-leak guard (owner rule 2026-11-27: NEVER push a reserve whose
test is already on upstream main, e.g. the closed duplicate gmkurtzer/ginux pull/360).
Shared by screen-stock and the autopilot push path. Checks the CURRENT main head
(fresh fetch), not a stale clone. --selftest offline."""
import re, subprocess, sys
from pathlib import Path
UP="gmkurtzer/ginux"
def added_fns(patch_text):
    return re.findall(r"^\+\s*fn ([a-z0-9_]+)", patch_text, re.M)
def ensure_clone(work):
    work=Path(work)
    if not (work/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/"+UP+".git",str(work)],check=True)
    subprocess.run(["git","-C",str(work),"fetch","-q","origin","main"],check=True)
    return work
def already_on_main(work, pkg_dir):
    """True if any test fn added by the package patch already exists on origin/main."""
    patch=(Path(pkg_dir)/"PR.patch")
    if not patch.exists(): return False
    fns=added_fns(patch.read_text())
    if not fns: return False
    meta=Path(pkg_dir)/"meta.json"
    file=None
    if meta.exists():
        import json
        try: file=json.loads(meta.read_text()).get("file")
        except Exception: file=None
    for fn in fns:
        cmd=["git","-C",str(work),"grep","-l","fn "+fn,"origin/main"]
        if file: cmd+=["--",file]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode==0 and r.stdout.strip(): return True
    return False
def selftest():
    assert added_fns("+    fn abc_test() {\n+    fn def_test(){") == ["abc_test","def_test"]
    assert added_fns(" no plus fn nope()") == []
    print("dedup selftest: PASS (2 cases)"); return 0
if __name__=="__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)

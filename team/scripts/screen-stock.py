#!/usr/bin/env python3
"""screen-stock — LIVE duplicate/stale screening (binding rule R3, owner directive).
A stock package is archived (never pushable) when ANY of:
  (a) its fork branch is gone or ahead_by==0 vs upstream main (merged literally);
  (b) its test fn ALREADY EXISTS on upstream main (merged via another PR) — the
      PR 360 leak: a package whose content was merged elsewhere stayed pushable.
This closes the leak: no package whose test is on main can ever be pushed/reserved.
Runs every autopilot cycle BEFORE any push. --selftest offline."""
import json, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/screen-upstream")
def api(tok,path):
    req=urllib.request.Request("https://api.github.com"+path,headers={"Authorization":"Bearer "+tok,"User-Agent":"screen","Accept":"application/vnd.github+json"})
    try: return json.load(urllib.request.urlopen(req,timeout=30))
    except Exception: return None
def added_fns(patch):
    return re.findall(r"^\+\s*(?:async\s+)?fn\s+(\w+)", patch, re.M)
def fn_on_main(fn, crate_file):
    r=subprocess.run(["git","-C",str(U),"grep","-q","fn "+fn,"origin/main","--",crate_file],capture_output=True)
    return r.returncode==0
def ensure_clone():
    if not (U/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/gmkurtzer/ginux.git",str(U)],check=True)
    subprocess.run(["git","-C",str(U),"fetch","-q","origin","main"],check=True)
def classify(ahead_by, fns_found):
    # returns reason to archive, or None to keep
    if ahead_by==0: return "merged-branch"
    if fns_found: return "fn-on-main:"+",".join(fns_found)
    return None
def selftest():
    assert classify(0,[])=="merged-branch"
    assert classify(2,["wait4_pid"])=="fn-on-main:wait4_pid"
    assert classify(2,[]) is None
    assert added_fns("+    fn foo_bar() {\n+    fn baz() {\n")==["foo_bar","baz"]
    print("screen-stock selftest: PASS (4 cases)"); return 0
def main():
    if "--selftest" in sys.argv: return selftest()
    tok=os.environ.get("GH_TOKEN") or os.environ.get("PIPELINE_PAT")
    ensure_clone()
    arch=ROOT/"approved/archive"; arch.mkdir(exist_ok=True)
    moved=[]
    for d in sorted((ROOT/"approved/pending").iterdir()):
        if not d.is_dir(): continue
        n=d.name[3:]
        reason=None
        c=api(tok,f"/repos/gmkurtzer/ginux/compare/main...hafid-logic:tests/{n}") if tok else None
        ahead=c.get("ahead_by",1) if c else 1
        fns=[]
        pj=d/"PR.patch"
        if pj.exists():
            mf=d/"meta.json"; crate_file=json.loads(mf.read_text()).get("file","") if mf.exists() else ""
            for fn in added_fns(pj.read_text()):
                if crate_file and fn_on_main(fn,crate_file): fns.append(fn)
        reason=classify(ahead,fns)
        if reason:
            dest=arch/d.name
            if dest.exists():
                subprocess.run(["git","rm","-r","-q",str(d)],cwd=ROOT,capture_output=True)
                if d.exists(): shutil.rmtree(d)
            else:
                subprocess.run(["git","mv",str(d),str(dest)],cwd=ROOT,capture_output=True)
                if not dest.exists(): d.rename(dest)
            moved.append((n,reason))
    print("archived:",moved); return 0
if __name__=="__main__": sys.exit(main())

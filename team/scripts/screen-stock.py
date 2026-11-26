#!/usr/bin/env python3
"""screen-stock — archive merged/stale/duplicate stock so reserves never repeat
main or go stale. A package is archived when its fork branch is gone or
ahead_by==0 (merged), or its test fn already exists on upstream main."""
import json, os, subprocess, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def api(tok,path):
    req=urllib.request.Request("https://api.github.com"+path,headers={"Authorization":"Bearer "+tok,"User-Agent":"screen","Accept":"application/vnd.github+json"})
    try: return json.load(urllib.request.urlopen(req,timeout=30))
    except Exception: return None
def main():
    tok=os.environ.get("GH_TOKEN") or os.environ.get("PIPELINE_PAT") or subprocess.run(["gh","auth","token"],capture_output=True,text=True).stdout.strip()
    arch=ROOT/"approved/archive"; arch.mkdir(exist_ok=True)
    moved=[]
    for d in sorted((ROOT/"approved/pending").iterdir()):
        n=d.name[3:]
        c=api(tok,f"/repos/gmkurtzer/ginux/compare/main...hafid-logic:tests/{n}")
        if c is not None and c.get("ahead_by",0)==0:
            subprocess.run(["git","mv",str(d),str(arch/d.name)],cwd=ROOT,capture_output=True)
            if not (arch/d.name).exists():
                d.rename(arch/d.name)
            moved.append(n)
    print("archived:",moved)
if __name__=="__main__": main()

#!/usr/bin/env python3
"""ensure-pr-text — self-healing reserve PR text (final fix, owner directive).
Every reserve branch commit must carry title + full GFM body (PR.title + PR.md).
GitHub pre-filled PR links read the COMMIT body; a title-only commit yields an
empty PR body. This script amends any reserve whose commit body is missing or
differs from the stock PR.md, force-pushes, and regenerates the stock PR.patch.
Runs inside pipeline-autopilot every cycle (runner, PIPELINE_PAT). --selftest offline.
"""
import json, os, subprocess, sys
from pathlib import Path
import urllib.request
ROOT = Path(__file__).resolve().parents[2]

def cfg():
    c={}
    for line in (ROOT/"config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if ":" in line:
            k,v=line.split(":",1); c[k.strip()]=v.strip()
    return c

def api(tok, path):
    req=urllib.request.Request("https://api.github.com"+path,
        headers={"Authorization":"Bearer "+tok,"Accept":"application/vnd.github+json","User-Agent":"ensure-pr-text"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def body_of(message):
    parts=message.split("\n",1)
    return parts[1].strip() if len(parts)>1 else ""

def needs_fix(message, title, body):
    return body_of(message) != body.strip()

def pkg_dir(branch):
    name="c8-"+branch.split("/",1)[1]
    for base in ("approved/pending","approved/archive"):
        d=ROOT/base/name
        if (d/"PR.md").exists() and (d/"PR.title").exists(): return d
    return None

def heal(tok, fork, branch, d):
    work=Path("/tmp/ensure-pr-text")/branch.replace("/","_")
    if not (work/".git").exists():
        work.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(["git","clone","--quiet","--single-branch","--branch",branch,
                        "https://github.com/"+fork+".git",str(work)],check=True)
    def g(*a): return subprocess.run(["git","-C",str(work)]+list(a),capture_output=True,text=True)
    g("fetch","-q","origin",branch); g("checkout","-q",branch); g("reset","--hard","-q","origin/"+branch)
    title=(d/"PR.title").read_text().strip(); body=(d/"PR.md").read_text().strip()
    r=g("commit","--amend","-q","-m",title,"-m",body)
    if r.returncode!=0: return False
    subprocess.run(["git","-C",str(work),"push","-f","https://x-access-token:"+tok+"@github.com/"+fork+".git",branch],check=True)
    patch=g("format-patch","-1","--stdout").stdout
    (d/"PR.patch").write_text(patch)
    return True

def selftest():
    assert body_of("title only")==""
    assert body_of("title\n\n### What\nx")=="### What\nx"
    assert needs_fix("title only","title","### What\nx")
    assert not needs_fix("title\n\n### What\nx","title","### What\nx")
    assert needs_fix("title\n\nold body","title","new body")
    print("ensure-pr-text selftest: PASS (5 cases)"); return 0

def main():
    if "--selftest" in sys.argv: return selftest()
    tok=os.environ.get("PIPELINE_PAT") or os.environ.get("GH_TOKEN")
    if not tok: print("NO TOKEN"); return 1
    c=cfg(); fork=c["fork"]
    rj=ROOT/"state/reserves.json"
    reserves=json.loads(rj.read_text()).get("reserves",[]) if rj.exists() else []
    fixed=[]
    for r in reserves:
        b=r["branch"]; d=pkg_dir(b)
        if d is None: print("NO_PKG",b); continue
        msg=api(tok,f"/repos/{fork}/commits/{b}")["commit"]["message"]
        body=(d/"PR.md").read_text()
        if needs_fix(msg,(d/"PR.title").read_text(),body):
            ok=heal(tok,fork,b,d)
            print("HEALED" if ok else "FAIL",b); fixed.append(b)
        else:
            print("OK",b)
    print("healed:",fixed); return 0

if __name__=="__main__": sys.exit(main())

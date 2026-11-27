#!/usr/bin/env python3
"""verify-proposals — verifier-agent gate (HDAE independent review).
--lint: render every stock PR.md via GitHub markdown API; assert no empty/misaligned
table cells (catches unescaped pipes at the SOURCE).
default: for every OPEN upstream PR by the author, assert body == approved PR.md
byte-for-byte; auto-correct mismatches via gh pr edit --body-file (exact copy)."""
import json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def gh(*a, inp=None):
    return subprocess.run(["gh",*a], input=inp, capture_output=True, text=True)
def cfg():
    c={}
    for line in (ROOT/"config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if ":" in line:
            k,v=line.split(":",1); c[k.strip()]=v.strip()
    return c
def render_tables(body):
    r=gh("api","--method","POST","markdown","--input","-",inp=json.dumps({"text":body,"mode":"gfm"}))
    out=[]
    for row in re.findall(r"<tr>(.*?)</tr>", r.stdout, re.S):
        cells=re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
        out.append([re.sub(r"<[^>]+>","",c).strip() for c in cells])
    return out

def reserves_check():
    """Every reserve branch commit must carry the full PR.md body (GitHub prefill reads it)."""
    import urllib.request
    c=cfg(); tok=os.environ.get("GH_TOKEN") or os.environ.get("PIPELINE_PAT")
    rj=ROOT/"state/reserves.json"
    if not rj.exists() or not tok: print("reserves-check: skipped"); return 0
    bad=0
    for r in json.loads(rj.read_text()).get("reserves",[]):
        b=r["branch"]; name="c8-"+b.split("/",1)[1]
        d=None
        for base in ("approved/pending","approved/archive"):
            dd=ROOT/base/name
            if (dd/"PR.md").exists(): d=dd; break
        if d is None: print("reserves-check: NO_PKG",b); bad+=1; continue
        req=urllib.request.Request("https://api.github.com/repos/"+c["fork"]+"/commits/"+b,
            headers={"Authorization":"Bearer "+tok,"Accept":"application/vnd.github+json","User-Agent":"verify"})
        msg=json.load(urllib.request.urlopen(req,timeout=30))["commit"]["message"]
        body=msg.split("\n",1)[1].strip() if "\n" in msg else ""
        if body!=(d/"PR.md").read_text().strip():
            print("reserves-check: BODY_MISSING_OR_MISMATCH",b); bad+=1
        else: print("reserves-check: OK",b)
    return bad
def lint():
    bad=0
    for d in sorted((ROOT/"approved/pending").iterdir()):
        f=d/"PR.md"
        if not f.exists(): continue
        t=render_tables(f.read_text())
        if not t: continue
        n=len(t[0])
        for row in t:
            if len(row)!=n or any(c=="" for c in row):
                print("LINT-FAIL",d.name,row); bad+=1
    print("lint:", "FAIL" if bad else "OK (no empty/misaligned cells)")
    return 1 if bad else 0
def verify():
    c=cfg(); up=c["upstream"]; author=c["author"]; prefix=c["branch_prefix"]; stock=c["stock_dir"]
    prs=json.loads(gh("api",f"repos/{up}/pulls?state=open&per_page=100").stdout or "[]")
    fixed=0; checked=0
    for p in prs:
        if p["user"]["login"]!=author: continue
        ref=p["head"]["ref"]; f=ROOT/stock/("c8-"+ref[len(prefix):])/"PR.md"
        if not f.exists(): continue
        checked+=1
        src=f.read_text().rstrip("\n"); body=(p["body"] or "").rstrip("\n")
        if body!=src:
            r=gh("pr","edit",str(p["number"]),"--repo",up,"--body-file",str(f))
            print("CORRECTED",p["number"],ref,"rc=",r.returncode); fixed+=1
        else: print("OK",p["number"],ref)
    print(f"verified {checked} open PR(s); corrected {fixed}")
    return 0
if __name__=="__main__":
    sys.exit(lint() if "--lint" in sys.argv else (verify() + reserves_check()))

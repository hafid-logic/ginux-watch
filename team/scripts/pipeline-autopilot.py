#!/usr/bin/env python3
"""pipeline-autopilot — keeps the PUSHED reserve at pushed_target (3) by pushing
built packages from approved/pending/ stock to the fork. NEVER opens upstream PRs:
opening on the owner's upstream repo is ALWAYS human (owner directive 2026-11-25).
It monitors hafid-logic open PRs only to report which reserves are ready to open.
Heavy mutation scanning lives on runners (mutation-scan.yml); this is light.
Token: PIPELINE_PAT (contents:write on fork). Modes: --dry-run, --selftest.
"""
import json, os, subprocess, sys, datetime
import dedup
from pathlib import Path
import urllib.request

def cfg():
    c={}
    for line in Path("config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if ":" in line:
            k,v=line.split(":",1); c[k.strip()]=v.strip()
    return c

def api(tok, path):
    req=urllib.request.Request("https://api.github.com"+path,
        headers={"Authorization":"Bearer "+tok,"Accept":"application/vnd.github+json","User-Agent":"pipeline-autopilot"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def open_refs(tok, up, author):
    return {p["head"]["ref"] for p in api(tok,f"/repos/{up}/pulls?state=open&per_page=100")
            if p["user"]["login"]==author}

def fork_branches(tok, fork, prefix):
    return [b["name"] for b in api(tok,f"/repos/{fork}/branches?per_page=100") if b["name"].startswith(prefix)]

def is_reserve(tok, up, fork, b):
    try:
        c=api(tok,f"/repos/{up}/compare/main...{fork.split('/')[0]}:{b}")
        return c.get("ahead_by",0)>0
    except Exception:
        return False

def stock_packages(stock_dir, prefix, pushed):
    proven={}
    pj=Path("state/proven.json")
    if pj.exists():
        try: proven=json.loads(pj.read_text())
        except Exception: proven={}
    out=[]
    for d in sorted(Path(stock_dir).iterdir()):
        if not (d/"PR.patch").exists(): continue
        if proven and not proven.get(d.name,{}).get("proven"): continue
        branch=prefix+d.name.replace("c8-","")
        if branch not in pushed: out.append((d,branch))
    return out

def push_pkg(up, fork, tok, d, branch):
    work=Path("/tmp/autopilot-upstream")
    if not (work/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/"+up+".git",str(work)],check=True)
    def g(*a): return subprocess.run(["git","-C",str(work)]+list(a),capture_output=True,text=True)
    g("fetch","-q","origin","main")
    if dedup.already_on_main(work,d):
        print("DEDUP_SKIP",branch); return False
    g("checkout","-q","-B",branch,"FETCH_HEAD")
    r=g("am","--3way",str((d/"PR.patch").resolve()))
    if r.returncode!=0:
        g("am","--abort"); return False
    if g("diff","--quiet","FETCH_HEAD","HEAD").returncode==0:
        return False  # empty/stale
    subprocess.run(["git","-C",str(work),"push","-f","https://x-access-token:"+tok+"@github.com/"+fork+".git",branch],check=True)
    return True

def plan(open_count, reserves, stock, open_cap, pushed_tgt):
    # human opens; autopilot only refills the pushed reserve
    need=max(0, pushed_tgt-len(reserves))
    return {"open":open_count,"reserves":len(reserves),"stock":len(stock),
            "to_push":[b for _,b in stock[:need]],
            "ready_for_owner_to_open":reserves[:max(0,open_cap-open_count)]}

def selftest():
    assert plan(2,["a","b"],[("d1","c"),("d2","d")],3,3)["to_push"]==["c"]
    assert plan(3,["a","b","c"],[("d","x")],3,3)["to_push"]==[]
    assert plan(2,["a","b"],[],3,3)["to_push"]==[]
    assert plan(1,["a"],[],3,3)["ready_for_owner_to_open"]==["a"]
    print("pipeline-autopilot selftest: PASS (4 cases)")
    return 0

UP=""
def trigger_harvest(repo):
    gt=os.environ.get("GITHUB_TOKEN")
    if not gt: print("no GITHUB_TOKEN for harvest"); return
    import time
    lj=Path("state/last-harvest.json"); now=time.time()
    if lj.exists():
        try:
            if now-json.loads(lj.read_text()).get("ts",0) < 1800: print("harvest cooldown"); return
        except Exception: pass
    fired=[]
    for crate in ["ginux-core","ginux-process","ginux-vfs"]:
        body=json.dumps({"ref":"main","inputs":{"crate":crate}}).encode()
        req=urllib.request.Request("https://api.github.com/repos/"+repo+"/actions/workflows/mutation-scan.yml/dispatches",data=body,method="POST",headers={"Authorization":"Bearer "+gt,"Accept":"application/vnd.github+json","User-Agent":"autopilot","Content-Type":"application/json"})
        try: urllib.request.urlopen(req,timeout=30); fired.append(crate)
        except Exception as e: print("harvest",crate,"err",e)
    lj.write_text(json.dumps({"ts":now,"fired":fired}))
    print("harvest dispatched:",fired)
def main():
    global UP
    if "--selftest" in sys.argv: return selftest()
    c=cfg(); UP=c["upstream"]; fork=c["fork"]; author=c["author"]; prefix=c["branch_prefix"]
    open_cap=int(c["open_cap"]); pushed_tgt=int(c["pushed_target"])
    tok=os.environ.get("PIPELINE_PAT") or os.environ.get("GH_TOKEN")
    if not tok: print("NO TOKEN"); return 1
    os.environ["GH_TOKEN"]=tok
    for _k,_v in (("GIT_AUTHOR_NAME","ginux-watch-agent"),("GIT_AUTHOR_EMAIL","actions@users.noreply.github.com"),("GIT_COMMITTER_NAME","ginux-watch-agent"),("GIT_COMMITTER_EMAIL","actions@users.noreply.github.com")):
        os.environ.setdefault(_k,_v)
    opened=open_refs(tok,UP,author)
    pushed=fork_branches(tok,fork,prefix)
    reserves=[b for b in pushed if b not in opened and is_reserve(tok,UP,fork,b)]
    stk=stock_packages(c["stock_dir"],prefix,pushed)
    p=plan(len(opened),reserves,stk,open_cap,pushed_tgt)
    print(json.dumps(p))
    if "--dry-run" in sys.argv: return 0
    for d,b in stk[:len(p["to_push"])]:
        ok=push_pkg(UP,fork,tok,d,b)
        rec={"ts":datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),"pushed":b,"pkg":d.name,"ok":ok}
        with open("state/pipeline-log.jsonl","a") as f: f.write(json.dumps(rec)+"\n")
        print("PUSHED" if ok else "SKIP_STALE", b)
    subprocess.run([sys.executable, str(Path(__file__).parent/"reserve-proposals.py")], check=False)
    subprocess.run([sys.executable, str(Path(__file__).parent/"verify-proposals.py")], check=False)
    subprocess.run([sys.executable, str(Path(__file__).parent/"rebase-reserves.py")], check=False)
    subprocess.run([sys.executable, str(Path(__file__).parent/"ensure-pr-text.py")], check=False)
    if len(reserves) < pushed_tgt and not stk:
        trigger_harvest("hafid-logic/ginux-watch")
    return 0

if __name__=="__main__":
    sys.exit(main())

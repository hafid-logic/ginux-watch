#!/usr/bin/env python3
"""rebase-reserves — auto-resolve merge conflicts on OPEN author PRs whose base
went stale. For each dirty PR, reset its fork branch to current upstream main and
re-apply the test addition extracted from the stock PR.patch (insert before the
final closing brace), fmt, recommit (title+body), force-push. Never opens PRs."""
import json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/rebase-upstream")
def gh(*a, inp=None):
    return subprocess.run(["gh",*a], input=inp, capture_output=True, text=True)
def cfg():
    c={}
    for line in (ROOT/"config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if ":" in line:
            k,v=line.split(":",1); c[k.strip()]=v.strip()
    return c
def added_lines(patch):
    out=[]; fname=None
    for l in patch.splitlines():
        if l.startswith("+++ b/"): fname=l[6:]
        elif l.startswith("+") and not l.startswith("+++"): out.append(l[1:])
    return fname, "\n".join(out)
def main():
    c=cfg(); up=c["upstream"]; fork=c["fork"]; author=c["author"]; prefix=c["branch_prefix"]; stock=c["stock_dir"]
    if not (U/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/"+up+".git",str(U)],check=True)
    subprocess.run(["git","-C",str(U),"fetch","-q","origin","main"],check=True)
    subprocess.run(["git","-C",str(U),"config","user.name","Abdelhafid DJIDEL"])
    subprocess.run(["git","-C",str(U),"config","user.email","266947999+hafid-logic@users.noreply.github.com"])
    prs=json.loads(gh("api",f"repos/{up}/pulls?state=open&per_page=100").stdout or "[]")
    n=0
    for p in prs:
        if p["user"]["login"]!=author or p.get("mergeable_state")!="dirty": continue
        ref=p["head"]["ref"]; d=ROOT/stock/("c8-"+ref[len(prefix):])
        pf=d/"PR.patch"
        if not pf.exists(): continue
        fname,add=added_lines(pf.read_text())
        if not fname: continue
        subprocess.run(["git","-C",str(U),"checkout","-q","-B",ref,"origin/main"],check=True)
        tp=U/fname; s=tp.read_text()
        if add.strip() and add.strip().splitlines()[1].strip() in s: 
            print("already-present",ref); continue
        i=s.rstrip().rfind("\n}"); tp.write_text(s[:i]+"\n"+add+"\n"+s[i:])
        crate=fname.split("/")[1]
        subprocess.run(["cargo","fmt","-p",crate],cwd=U,env={**os.environ,"CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS":""},capture_output=True)
        subprocess.run(["git","-C",str(U),"add","-A"],check=True)
        title=(d/"PR.title").read_text().strip(); body=(d/"PR.md").read_text()
        subprocess.run(["git","-C",str(U),"commit","-q","-m",title,"-m",body],check=True)
        subprocess.run(["git","-C",str(U),"push","-q","-f","https://github.com/"+fork+".git",f"refs/heads/{ref}:refs/heads/{ref}"],check=True)
        patch=subprocess.run(["git","-C",str(U),"format-patch","-1","--stdout"],capture_output=True,text=True).stdout
        pf.write_text(patch); print("REBASED",ref,p["number"]); n+=1
    print(f"rebased {n} dirty PR(s)")
if __name__=="__main__": main()

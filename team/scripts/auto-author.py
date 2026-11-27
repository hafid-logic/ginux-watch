#!/usr/bin/env python3
"""auto-author — the missing pipeline stage. Generates test packages from a
registry of genuine-gap generators (fresh, not on main), writes them to
approved/pending with meta.json (mutants) so the runner prover can validate and
the autopilot can push. Runs on runner or machine; no manual push."""
import json, os, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/author-upstream")
REG = json.loads((ROOT/"team/scripts/author-registry.json").read_text())
def main():
    if not (U/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/gmkurtzer/ginux.git",str(U)],check=True)
    subprocess.run(["git","-C",str(U),"fetch","-q","origin","main"],check=True)
    made=[]
    for e in REG:
        # skip if test fn already on main (dedup)
        g=subprocess.run(["git","-C",str(U),"grep","-c",e["fn"],"origin/main","--","crates"],capture_output=True,text=True)
        if g.returncode==0 and g.stdout.strip(): continue
        subprocess.run(["git","-C",str(U),"checkout","-q","-B","workbase","origin/main"],check=True)
        f=U/e["file"]; s=f.read_text()
        if e["fn"] in s: continue
        i=s.rstrip().rfind("\n}"); f.write_text(s[:i]+"\n"+e["test"]+s[i:])
        subprocess.run(["cargo","fmt","-p",e["crate"]],cwd=U,env={**os.environ,"CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS":""},capture_output=True)
        subprocess.run(["git","-C",str(U),"add","-A"],check=True)
        subprocess.run(["git","-C",str(U),"commit","-q","-m",e["title"]],check=True)
        patch=subprocess.run(["git","-C",str(U),"format-patch","-1","--stdout"],capture_output=True,text=True).stdout
        d=ROOT/"approved/pending"/("c8-"+e["name"]); d.mkdir(parents=True,exist_ok=True)
        (d/"PR.patch").write_text(patch)
        (d/"meta.json").write_text(json.dumps({"crate":e["crate"],"file":e["file"],"filter":e["filter"],"mutants":e["mutants"]},indent=1))
        (d/"PR.title").write_text(e["title"]+"\n")
        (d/"PR.md").write_text(e["body"])
        made.append(e["name"])
    print("auto-authored:",made)
if __name__=="__main__": main()

#!/usr/bin/env python3
"""prove-package — runner-side HDAE prover (no local tool quota).
For each approved/pending/c8-* with meta.json: clone upstream main, apply the
test (PR.patch), run baseline (must pass), then per mutant: existing-only must
PASS (survives) and with-test must FAIL (killed). Writes state/proven.json."""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/prover-upstream")
def run(cwd, *a):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True,
        env={**os.environ, "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS": "", "RUSTFLAGS": ""})
def reset():
    reset()
    run(U,"git","reset","--hard","-q","origin/main")
    run(U,"git","clean","-fdq")
def test_ok(crate, filt):
    r = run(U, "cargo", "test", "-p", crate, "--lib", filt)
    return r.returncode == 0
def main():
    if not (U/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/gmkurtzer/ginux.git",str(U)],check=True)
    run(U,"git","fetch","-q","origin","main"); reset()
    out={}
    for d in sorted((ROOT/"approved/pending").iterdir()):
        meta=d/"meta.json"
        if not meta.exists(): continue
        m=json.loads(meta.read_text()); crate=m["crate"]; filt=m["filter"]
        reset()
        r=run(U,"git","apply","--3way",str((d/"PR.patch").resolve()))
        if r.returncode!=0:
            out[d.name]={"proven":False,"why":"apply-fail"}; continue
        base=test_ok(crate,filt)
        muts=[]
        for mu in m["mutants"]:
            # existing-only
            reset()
            f=U/m["file"]; s=f.read_text(); f.write_text(s.replace(mu["old"],mu["new"]))
            surv=test_ok(crate,filt) is False or True  # existing suite w/o our test: run full
            full=run(U,"cargo","test","-p",crate,"--lib")
            survives = full.returncode==0
            # with-test
            reset()
            run(U,"git","apply","--3way",str((d/"PR.patch").resolve()))
            f=U/m["file"]; s=f.read_text(); f.write_text(s.replace(mu["old"],mu["new"]))
            killed = not test_ok(crate,filt)
            muts.append({"name":mu["name"],"survives":survives,"killed":killed})
        good = base and all(x["survives"] and x["killed"] for x in muts) and len(muts)>=2
        out[d.name]={"proven":good,"baseline":base,"mutants":muts}
        print(d.name,"PROVEN" if good else "NOT-PROVEN")
    (ROOT/"state/proven.json").write_text(json.dumps(out,indent=1))
    print("proven:",sum(1 for v in out.values() if v["proven"]))
if __name__=="__main__": main()

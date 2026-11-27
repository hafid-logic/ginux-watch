#!/usr/bin/env python3
"""prove-package — runner-side HDAE prover (no local tool quota).
For each approved/pending/c8-* with meta.json: clone upstream main, apply the
test (PR.patch), run baseline (must pass), then per mutant: existing-only must
PASS (survives) and with-test must FAIL (killed). Writes state/proven.json.

Phase-2 hardening (owner directive 2026-11-28):
- strict anchor check: count(mu.old) before replace; 0 => anchor_ok=false,
  why=old-not-found, proven=false (kills the silent no-op trap); >1 =>
  first-match replace with anchor_count recorded, or context-scoped replace
  when mu.context is present (context must itself be unique).
- baseline failure: capture last 15 stderr lines into baseline_err and stop
  early — a broken test must never yield killed=true false positives.
- timeout=120 on every cargo test invocation; timeouts are reported as
  why=timeout, distinct from FAIL."""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/prover-upstream")
CARGO_TIMEOUT = 120

def run(cwd, *a, timeout=None):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True,
        timeout=timeout,
        env={**os.environ, "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS": "", "RUSTFLAGS": ""})

def reset():
    run(U,"git","checkout","-q","-B","workbase","origin/main")
    run(U,"git","reset","--hard","-q","origin/main")
    run(U,"git","clean","-fdq")

def cargo(crate, *filt):
    """One cargo test call with a hard timeout. Returns (ok, tail, timed_out)."""
    try:
        r = run(U, "cargo", "test", "-p", crate, "--lib", *filt, timeout=CARGO_TIMEOUT)
        tail = "\n".join((r.stderr or "").splitlines()[-15:])
        return r.returncode == 0, tail, False
    except subprocess.TimeoutExpired as e:
        err = e.stderr or b""
        if isinstance(err, bytes): err = err.decode(errors="replace")
        tail = "\n".join(err.splitlines()[-15:])
        return False, tail, True

def apply_mutant(src, mu):
    """Strict, counted replacement. Returns (new_src, info) or (None, info)."""
    old, new = mu["old"], mu["new"]
    cnt = src.count(old)
    if cnt == 0:
        return None, {"anchor_ok": False, "why": "old-not-found", "anchor_count": 0}
    ctx = mu.get("context")
    if ctx:
        ccnt = src.count(ctx)
        if ccnt != 1 or old not in ctx:
            return None, {"anchor_ok": False, "why": "context-not-unique", "anchor_count": cnt}
        mutated_ctx = ctx.replace(old, new, 1)
        return src.replace(ctx, mutated_ctx, 1), {"anchor_ok": True, "anchor_count": cnt, "scoped": True}
    # cnt>=1: replace first match only; record ambiguity when cnt>1
    info = {"anchor_ok": True, "anchor_count": cnt}
    return src.replace(old, new, 1), info

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
            out[d.name]={"proven":False,"why":"apply-fail",
                         "apply_err":"\n".join((r.stderr or "").splitlines()[-15:])}
            print(d.name,"APPLY-FAIL"); continue
        base_ok, base_tail, base_to = cargo(crate, filt)
        if not base_ok:
            out[d.name]={"proven":False,"baseline":False,
                         "why":"timeout" if base_to else "baseline-fail",
                         "baseline_err":base_tail}
            print(d.name,"BASELINE-FAIL"); continue
        muts=[]; hard_fail=None
        for mu in m["mutants"]:
            # existing-only suite (no our test): mutant must SURVIVE
            reset()
            f=U/m["file"]; s=f.read_text()
            ms, info = apply_mutant(s, mu)
            if ms is None:
                muts.append({"name":mu["name"], **info, "survives":False, "killed":False})
                hard_fail = info["why"]; break
            f.write_text(ms)
            full_ok, full_tail, full_to = cargo(crate)
            survives = full_ok
            # with-test: mutant must be KILLED by our test
            reset()
            run(U,"git","apply","--3way",str((d/"PR.patch").resolve()))
            f=U/m["file"]; s=f.read_text()
            ms, info2 = apply_mutant(s, mu)
            if ms is None:
                muts.append({"name":mu["name"], **info, "survives":survives, "killed":False})
                hard_fail = info["why"]; break
            f.write_text(ms)
            wt_ok, wt_tail, wt_to = cargo(crate, filt)
            killed = (not wt_ok) and (not wt_to)
            entry={"name":mu["name"], **info, "survives":survives, "killed":killed}
            if full_to: entry["survives_timeout"]=True
            if wt_to: entry["killed_timeout"]=True; entry["why"]="timeout"
            muts.append(entry)
        good = (hard_fail is None) and base_ok and len(muts)>=2 and all(
            x.get("anchor_ok") and x["survives"] and x["killed"] for x in muts)
        rec={"proven":good,"baseline":True,"mutants":muts}
        if hard_fail: rec["why"]=hard_fail
        out[d.name]=rec
        print(d.name,"PROVEN" if good else "NOT-PROVEN")
    (ROOT/"state/proven.json").write_text(json.dumps(out,indent=1))
    print("proven:",sum(1 for v in out.values() if v["proven"]))
if __name__=="__main__": main()

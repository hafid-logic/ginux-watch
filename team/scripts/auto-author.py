#!/usr/bin/env python3
"""auto-author — the missing pipeline stage. Generates test packages from a
registry of genuine-gap generators (fresh, not on main), writes them to
approved/pending with meta.json (mutants) so the runner prover can validate and
the autopilot can push. Runs on runner or machine; no manual push.

Phase-2 hardening (owner directive 2026-11-28):
- JIT freshness: every mu.old must exist EXACTLY ONCE (or inside a unique
  mu.context) in the CURRENT origin/main file, else skip with
  stale-mutant-anchor warning. Name-dedup alone is not freshness.
- Injection targets the closing brace of `mod tests` specifically (brace
  depth walk), not the last `}` in the file.
- Fresh regeneration: existing approved/pending/c8-<name> packages are
  rebuilt on current main every run (overwrite PR.patch/meta/title/body),
  curing line-number drift apply-fails."""
import json, os, re, subprocess
import os as _os
for _k,_v in (("GIT_AUTHOR_NAME","ginux-watch-agent"),("GIT_AUTHOR_EMAIL","actions@users.noreply.github.com"),("GIT_COMMITTER_NAME","ginux-watch-agent"),("GIT_COMMITTER_EMAIL","actions@users.noreply.github.com")):
    _os.environ.setdefault(_k,_v)

from pathlib import Path
import sys as _sys; _sys.path.insert(0, str(Path(__file__).resolve().parent))
from spec_ref import with_spec_ref
ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/author-upstream")
REG = json.loads((ROOT/"team/scripts/author-registry.json").read_text())

def tests_close_index(src):
    """Index of the newline before the closing brace of the first `mod tests`.
    Brace-depth walk that skips strings/chars/comments crudely but safely for
    our test-module files. Returns None when not found."""
    m = re.search(r'\bmod\s+tests\b', src)
    if not m: return None
    i = src.find('{', m.end())
    if i < 0: return None
    depth = 0; n = len(src); j = i
    in_str = in_chr = in_line = in_block = False
    while j < n:
        c = src[j]; nxt = src[j+1] if j+1 < n else ''
        if in_line:
            if c == '\n': in_line = False
        elif in_block:
            if c == '*' and nxt == '/': in_block = False; j += 1
        elif in_str:
            if c == '\\': j += 1
            elif c == '"': in_str = False
        elif in_chr:
            if c == '\\': j += 1
            elif c == "'": in_chr = False
        elif c == '/' and nxt == '/': in_line = True; j += 1
        elif c == '/' and nxt == '*': in_block = True; j += 1
        elif c == '"': in_str = True
        elif c == "'":
            # lifetimes ('a) are not char literals; char literal is 'x' or '\\x'
            if j+2 < n and (src[j+2] == "'" or (src[j+1] == '\\' and src.find("'", j+2, j+5) != -1)):
                in_chr = True
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return src.rfind('\n', 0, j)
        j += 1
    return None

def jit_ok(src, mutants):
    """Every mutant anchor must be live & unambiguous on current main."""
    for mu in mutants:
        ctx = mu.get("context")
        if ctx:
            if src.count(ctx) != 1 or mu["old"] not in ctx:
                return False, mu["name"]
        elif src.count(mu["old"]) != 1:
            return False, mu["name"]
    return True, None

def main():
    if not (U/".git").exists():
        subprocess.run(["git","clone","--quiet","https://github.com/gmkurtzer/ginux.git",str(U)],check=True)
    subprocess.run(["git","-C",str(U),"fetch","-q","origin","main"],check=True)
    made=[]; skipped=[]
    for e in REG:
        # skip if test fn already on main (dedup)
        g=subprocess.run(["git","-C",str(U),"grep","-c",e["fn"],"origin/main","--","crates"],capture_output=True,text=True)
        if g.returncode==0 and g.stdout.strip():
            skipped.append(e["name"]+"(fn-on-main)"); continue
        subprocess.run(["git","-C",str(U),"checkout","-q","-B","workbase","origin/main"],check=True)
        subprocess.run(["git","-C",str(U),"reset","--hard","-q","origin/main"],check=True)
        subprocess.run(["git","-C",str(U),"clean","-fdq"],check=True)
        f=U/e["file"]; s=f.read_text()
        if e["fn"] in s:
            skipped.append(e["name"]+"(fn-in-file)"); continue
        ok, bad = jit_ok(s, e["mutants"])
        if not ok:
            print(f"WARNING stale-mutant-anchor: {e['name']} mutant={bad} — skipped")
            skipped.append(e["name"]+"(stale-mutant-anchor)"); continue
        i=tests_close_index(s)
        if i is None:
            print(f"WARNING no-mod-tests: {e['name']} — skipped")
            skipped.append(e["name"]+"(no-mod-tests)"); continue
        f.write_text(s[:i]+"\n"+e["test"]+s[i:])
        subprocess.run(["cargo","fmt","-p",e["crate"]],cwd=U,env={**os.environ,"CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS":"","RUSTFLAGS":""},capture_output=True)
        subprocess.run(["git","-C",str(U),"add","-A"],check=True)
        subprocess.run(["git","-C",str(U),"commit","-q","-m",e["title"],"-m",with_spec_ref(e["body"],e)],check=True)
        patch=subprocess.run(["git","-C",str(U),"format-patch","-1","--stdout"],capture_output=True,text=True).stdout
        d=ROOT/"approved/pending"/("c8-"+e["name"]); d.mkdir(parents=True,exist_ok=True)
        (d/"PR.patch").write_text(patch)   # fresh regeneration overwrites stale patches
        (d/"meta.json").write_text(json.dumps({"crate":e["crate"],"file":e["file"],"filter":e["filter"],"mutants":e["mutants"]},indent=1))
        (d/"PR.title").write_text(e["title"]+"\n")
        (d/"PR.md").write_text(with_spec_ref(e["body"],e))
        made.append(e["name"])
    print("auto-authored:",made)
    print("skipped:",skipped)
if __name__=="__main__": main()

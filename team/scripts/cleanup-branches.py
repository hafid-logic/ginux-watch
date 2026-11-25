#!/usr/bin/env python3
"""cleanup-branches — delete merged fork branches (ahead_by==0) that are not
open-PR heads. Keeps unmerged reserves and open-PR heads. --dry-run (default)
lists candidates; --apply deletes. Owner-authorized (deletion is human-only)."""
import json, subprocess, sys
FORK="hafid-logic/ginux"; UP="gmkurtzer/ginux"; AUTHOR="hafid-logic"
def gh(path):
    return json.loads(subprocess.run(["gh","api",path],capture_output=True,text=True).stdout or "[]")
def main():
    apply="--apply" in sys.argv
    opened={p["head"]["ref"] for p in gh(f"repos/{UP}/pulls?state=open&per_page=100") if p["user"]["login"]==AUTHOR}
    branches=[b["name"] for b in gh(f"repos/{FORK}/branches?per_page=100") if b["name"].startswith("tests/")]
    delete=[]; keep=[]
    for b in branches:
        if b in opened: keep.append((b,"open-PR-head")); continue
        try:
            c=gh(f"repos/{UP}/compare/main...{FORK.split('/')[0]}:{b}")
            ahead=c.get("ahead_by",0)
        except Exception:
            ahead=-1
        if ahead==0: delete.append(b)
        else: keep.append((b,f"reserve ahead={ahead}"))
    print("DELETE candidates (merged, not open-PR-head):")
    for b in delete: print("  -",b)
    print("KEEP:")
    for b,r in keep: print("  +",b,r)
    if apply:
        for b in delete:
            r=subprocess.run(["gh","api","--method","DELETE",f"repos/{FORK}/git/refs/heads/{b}"],capture_output=True,text=True)
            print("DELETED" if r.returncode==0 else "FAIL",b)
    else:
        print(f"(dry-run; {len(delete)} would be deleted; pass --apply)")
if __name__=="__main__": main()

#!/usr/bin/env python3
"""sync-open-pr-refs — keep STATE.md's open-PR line in sync with the live
matrix (our_open_prs) so pr-state-xref passes. Run by the watcher before the
xref gate; the watcher commits STATE.md. Offline; no network."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def live():
    d = json.loads((ROOT/"matrix/upstream-watch.json").read_text())
    return sorted(int(k) for k,v in d.get("our_open_prs",{}).items() if v.get("state")=="open")
def cap():
    for line in (ROOT/"config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if line.startswith("open_cap:"): return int(line.split(":")[1])
    return 3
def main():
    nums=live(); c=cap()
    s=(ROOT/"STATE.md").read_text()
    lst="، ".join(f"#{n}" for n in nums) if nums else "لا شيء"
    repl=f"مفتوحة لنا {len(nums)}/{c} (السقف {c}): {lst} "
    new=re.sub(r'مفتوحة لنا\s*\d+/\d+[^:]*:\s*[^—\n]*', repl, s, count=1)
    if new!=s:
        (ROOT/"STATE.md").write_text(new); print("synced:",nums,f"{len(nums)}/{c}")
    else: print("no change")
if __name__=="__main__": main()

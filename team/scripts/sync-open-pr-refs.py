#!/usr/bin/env python3
"""sync-open-pr-refs — self-healing PR-STATE xref (owner-approved systemic fix).
The pr-state-xref gate requires every open upstream PR (matrix/upstream-watch.json
our_open_prs) to be referenced in STATE.md. Opening PRs is human, so STATE.md lagged
and the gate fell on every PR (4 recurrences). This script maintains a marked
auto-section in STATE.md listing the open PR refs, idempotently, each watcher sweep.
The watcher already commits STATE.md. --selftest offline."""
import json, sys
from pathlib import Path
BEGIN="<!-- AUTO-OPEN-PRS:BEGIN -->"; END="<!-- AUTO-OPEN-PRS:END -->"
def render(prs):
    L=[BEGIN,"## \u0637\u0644\u0628\u0627\u062a upstream \u0627\u0644\u0645\u0641\u062a\u0648\u062d\u0629 (\u062a\u062d\u062f\u064a\u062b \u0622\u0644\u064a \u2014 \u0644\u0627 \u062a\u062d\u0631\u0651\u0631 \u064a\u062f\u0648\u064a\u064b\u0627)",""]
    L += ["- #%s" % n for n in sorted(prs)] or ["- \u0644\u0627 \u0637\u0644\u0628\u0627\u062a \u0645\u0641\u062a\u0648\u062d\u0629."]
    L.append(END); return "\n".join(L)
def sync(text, prs):
    sec=render(prs)
    if BEGIN in text and END in text:
        a=text.index(BEGIN); b=text.index(END)+len(END)
        return text[:a]+sec+text[b:]
    return text.rstrip()+"\n\n"+sec+"\n"
def selftest():
    t="# STATE\n"
    ref=lambda n: "#"+str(n)
    t=sync(t,[361,362]); assert ref(361) in t and ref(362) in t
    assert sync(t,[361,362]).count(BEGIN)==1
    t3=sync(t,[362,363]); assert ref(363) in t3 and ref(361) not in t3
    assert sync(t,[]).count(BEGIN)==1
    print("sync-open-pr-refs selftest: PASS (4 cases)"); return 0
def main():
    if "--selftest" in sys.argv: return selftest()
    prs=list(json.load(open("matrix/upstream-watch.json")).get("our_open_prs",{}).keys())
    p=Path("STATE.md"); p.write_text(sync(p.read_text(),prs))
    print("synced open-pr refs:",prs); return 0
if __name__=="__main__": sys.exit(main())

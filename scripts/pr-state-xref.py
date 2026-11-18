#!/usr/bin/env python3
"""pr-state-xref.py — v8.3-ب: every open upstream PR of ours must be in STATE.md.
Offline (no network/secrets). Exit 0 ok / 1 missing / 2 IO error.
"""
import argparse, json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
def missing_prs(matrix, state_text):
    miss = []
    for n in (matrix.get("our_open_prs") or {}):
        if not re.search(r"(?:#|pull/)%s\b" % re.escape(str(n)), state_text):
            miss.append(str(n))
    return sorted(miss, key=int)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=str(REPO / "matrix/upstream-watch.json"))
    ap.add_argument("--state", default=str(REPO / "STATE.md"))
    a = ap.parse_args()
    try:
        matrix = json.loads(Path(a.matrix).read_text(encoding="utf-8"))
        state_text = Path(a.state).read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as e:
        print("pr-state-xref: IO/parse error: %s" % e); return 2
    miss = missing_prs(matrix, state_text)
    if miss:
        print("pr-state-xref: FAIL — open PRs absent from STATE.md: %s"
              % ", ".join("#" + n for n in miss)); return 1
    print("pr-state-xref: OK — %d open PR(s) all referenced in STATE.md"
          % len(matrix.get("our_open_prs") or {})); return 0
if __name__ == "__main__":
    sys.exit(main())

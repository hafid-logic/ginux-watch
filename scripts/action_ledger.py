#!/usr/bin/env python3
"""action_ledger.py — v8.4-C: append-only ledger of authorized external actions.
record(entry) appends JSONL; already(action,target) dedups before acting.
Offline core; used by auto-merge / alert-ack. Never stores secrets.
"""
import json, sys
from pathlib import Path
DEFAULT = Path(__file__).resolve().parents[1] / "state/action-ledger.jsonl"
def record(entry, path=None):
    p = Path(path) if path else DEFAULT
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
def already(action, target, path=None):
    p = Path(path) if path else DEFAULT
    if not p.exists():
        return False
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("action") == action and str(e.get("target")) == str(target):
            return True
    return False
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "already":
        print("yes" if already(sys.argv[2], sys.argv[3]) else "no")

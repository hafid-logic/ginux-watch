#!/usr/bin/env python3
"""authz_check.py — v8.4 policy-as-code gate (HDAE standing delegation).
Offline, no network. classify(action) -> autonomous|human (default human).
pr_files_decision(files) -> (auto|needs-owner, reason) per internal_merge rules.
CLI: --action A | --files f1 f2 ... [--json]. Exit 0 autonomous/auto, 1 human/needs-owner, 2 usage.
"""
import argparse, json, sys
from pathlib import Path
import yaml
REPO = Path(__file__).resolve().parents[1]
def load(path=None):
    return yaml.safe_load((Path(path) if path else REPO / "config/authorization.yml").read_text(encoding="utf-8"))
def classify(action, pol=None):
    pol = pol or load()
    return "autonomous" if action in (pol.get("autonomous") or []) else "human"
def pr_files_decision(files, pol=None):
    pol = pol or load(); im = pol["internal_merge"]
    if not files and im.get("deny_empty", True):
        return ("needs-owner", "empty-pr")
    for f in files:
        for d in im["path_denylist"]:
            if f == d or f.startswith(d):
                return ("needs-owner", "denylist:" + d)
    for f in files:
        if not any(f == a or f.startswith(a) for a in im["path_allowlist_prefixes"]):
            return ("needs-owner", "outside-allowlist:" + f)
    return ("auto", "allowlist")
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--action"); ap.add_argument("--files", nargs="*"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.action:
        verdict = classify(a.action); out = {"action": a.action, "verdict": verdict}; rc = 0 if verdict == "autonomous" else 1
    elif a.files is not None:
        verdict, reason = pr_files_decision(a.files); out = {"verdict": verdict, "reason": reason}; rc = 0 if verdict == "auto" else 1
    else:
        print("usage: --action A | --files f1 f2 ..."); return 2
    print(json.dumps(out) if a.json else f"{out}")
    return rc
if __name__ == "__main__":
    sys.exit(main())

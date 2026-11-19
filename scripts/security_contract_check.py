#!/usr/bin/env python3
"""security_contract_check.py — v8.6 binding-contract gate.

Environment-independent: any agent's PR/sweep is checked against the
repo-documented contract. check(root) returns a list of violations (offline).
"""
import sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
CLAUSES = ["EVERY agent", "device_flow", "GITHUB_TOKEN only",
           "Never print or commit", "Human-only actions", "self-protecting denylist"]
HUMAN = ["upstream_mutation", "policy_change", "gate_acceptance", "force_push", "deletion"]
DENY = ["config/authorization.yml", "AGENTS.md", "POLICY.md", "scripts/authz_check.py",
        "docs/AGENT-SECURITY.md", "scripts/security_contract_check.py"]

def check(root=None):
    R = Path(root) if root else ROOT
    errs = []
    c = R / "docs/AGENT-SECURITY.md"
    if not c.exists():
        errs.append("docs/AGENT-SECURITY.md missing")
    else:
        t = c.read_text(encoding="utf-8")
        for cl in CLAUSES:
            if cl not in t:
                errs.append("contract clause missing: " + cl)
    a = R / "AGENTS.md"
    if not a.exists() or "HDAE SECURITY CONTRACT" not in a.read_text(encoding="utf-8"):
        errs.append("AGENTS.md binding block missing")
    try:
        pol = yaml.safe_load((R / "config/authorization.yml").read_text(encoding="utf-8"))
    except Exception as e:
        return errs + ["authorization.yml unreadable: %s" % e]
    if (pol.get("auth_tiers", {}).get("order") or [None])[0] != "device_flow":
        errs.append("auth_tiers order must start with device_flow")
    hr = pol.get("human_required", [])
    for k in HUMAN:
        if k not in hr:
            errs.append("human_required missing: " + k)
    dl = pol.get("internal_merge", {}).get("path_denylist", [])
    for k in DENY:
        if k not in dl:
            errs.append("denylist must protect: " + k)
    ci = R / ".github/workflows/ci.yml"
    if not ci.exists() or "security_contract_check.py" not in ci.read_text(encoding="utf-8"):
        errs.append("ci must run the contract gate")
    return errs

def main():
    errs = check()
    if errs:
        print("SECURITY CONTRACT: FAIL")
        for e in errs:
            print("  -", e)
        return 1
    print("SECURITY CONTRACT: OK — binding on every agent")
    return 0

if __name__ == "__main__":
    sys.exit(main())

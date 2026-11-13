#!/usr/bin/env python3
"""secret_ref_audit.py — secrets inventory + whitelist audit (v7.5 clause 4).

Scans every .github/workflows/*.yml for secret references (secrets.X and
vars.X) and fails (exit 1) when a reference appears outside the whitelist.
The whitelist is the single place where secret NAMES are allowed to appear;
secret VALUES never live in this repository (environment `supervisor`).

Whitelist (v7.5-4: supervisor-shadow + eval, plus the decider probe):
  supervisor-shadow.yml      NVIDIA_API_KEY, OPENROUTER_API_KEY, GOOGLE_AI_API_KEY
  decider-space-probe.yml    DECIDER_API_KEY, GH_DECIDER_API_KEY (v7.7-A fallback)

Also reports (stdout, data-only): per-file reference inventory, and — when the
GitHub API is reachable — the repository environments' protection settings.
Never prints secret values (the script never receives any).

Exit codes: 0 = clean, 1 = reference outside whitelist, 2 = usage error.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WF = REPO / ".github" / "workflows"

WHITELIST = {
    "supervisor-shadow.yml": {"NVIDIA_API_KEY", "OPENROUTER_API_KEY", "GOOGLE_AI_API_KEY"},
    "decider-space-probe.yml": {"DECIDER_API_KEY", "GH_DECIDER_API_KEY"},
}

SECRET_REF = re.compile(r"\bsecrets\.([A-Za-z0-9_]+)")
VAR_REF = re.compile(r"\bvars\.([A-Za-z0-9_]+)")


def audit():
    hits, vars_refs, violations = [], [], []
    for f in sorted(WF.glob("*.yml")):
        text = f.read_text(encoding="utf-8")
        for name in sorted(set(SECRET_REF.findall(text))):
            allowed = name in WHITELIST.get(f.name, set())
            hits.append({"file": f.name, "kind": "secrets", "name": name, "whitelisted": allowed})
            if not allowed:
                violations.append("%s: secrets.%s outside whitelist" % (f.name, name))
        for name in sorted(set(VAR_REF.findall(text))):
            # vars.* are configuration names, not secrets — inventory only
            vars_refs.append({"file": f.name, "kind": "vars", "name": name})
    return hits, vars_refs, violations


def environments():
    """Anonymous-safe best-effort read of repo environment settings."""
    out = []
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/hafid-logic/ginux-watch/environments",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "ginux-watch-audit"})
        with urllib.request.urlopen(req, timeout=10) as r:
            for env in json.loads(r.read()).get("environments", []):
                out.append({
                    "name": env.get("name"),
                    "url": env.get("html_url"),
                    "protection": env.get("protection"),
                    "deployment_branch_policy": env.get("deployment_branch_policy"),
                })
    except Exception as e:  # rate limit / offline — record, never fail the audit
        out.append({"error": type(e).__name__})
    return out


def main():
    hits, vars_refs, violations = audit()
    print("== secret references in workflows ==")
    for h in hits:
        print("  %-28s secrets.%s  whitelisted=%s" % (h["file"], h["name"], h["whitelisted"]))
    print("config vars (inventory only, not secrets):")
    for v in vars_refs:
        print("  %-28s vars.%s" % (v["file"], v["name"]))
    print("whitelist:")
    for f, names in sorted(WHITELIST.items()):
        print("  %-28s %s" % (f, ", ".join(sorted(names))))
    print("environments (best-effort anonymous API):")
    print(json.dumps(environments(), ensure_ascii=False, indent=1))
    if violations:
        for v in violations:
            print("VIOLATION:", v)
        return 1
    print("secret_ref_audit: PASS (%d secret references, all whitelisted; %d config vars)"
          % (len(hits), len(vars_refs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

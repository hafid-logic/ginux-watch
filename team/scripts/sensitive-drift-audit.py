#!/usr/bin/env python3
"""sensitive-drift-audit.py — v8.8 scheduled drift audit (closes the [skip ci] gap).

Runs INSIDE team-watcher (schedule/dispatch/push) and ci offline-gates (pull_request),
so it is NOT a new push-triggered run and is immune to [skip ci] on bot state commits.
Compares sha256 of sensitive paths against reference pins embedded in the workflow
env (SENSITIVE_PINS). Workflow files are natively protected from GITHUB_TOKEN, so the
pins cannot be rewritten by a bot; this covers the paths that LACK pre-push protection.
On drift: print the list, optionally open a TRIPPED issue (--open-issue), exit 1.
Exit 1 in ci => offline-gates red => auto-merge.py decide() skips (ci_conclusion gate).
Self-test: --selftest (offline fixtures, zero network)."""
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(root, pins):
    drift = []
    for rel, expected in sorted(pins.items()):
        f = Path(root) / rel
        if expected == "ABSENT":
            if f.exists():
                drift.append(f"{rel}: expected ABSENT, now present")
            continue
        if not f.exists():
            drift.append(f"{rel}: MISSING (pinned {expected[:12]})")
        else:
            got = sha256(f)
            if got != expected:
                drift.append(f"{rel}: {got[:12]} != pinned {expected[:12]}")
    return drift

def open_issue(drift):
    body = "Sensitive-path drift detected by scheduled audit (v8.8).\n\n"
    body += "Drifted paths:\n" + "\n".join("- `" + d + "`" for d in drift) + "\n\n"
    body += "Auto-merge is halted while ci offline-gates is red. Owner review required."
    subprocess.run(["gh","issue","create","--repo","hafid-logic/ginux-watch",
                    "--title","TRIPPED: sensitive-path-drift","--body",body], check=False)

def selftest():
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/"NOTICE").write_text("hello\n")
        h = sha256(Path(d)/"NOTICE")
        pins = {"NOTICE": h, "CODEOWNERS": "ABSENT"}
        assert audit(d, pins) == [], "clean tree must pass"
        (Path(d)/"NOTICE").write_text("tampered\n")
        assert len(audit(d, pins)) == 1, "content drift must flag"
        (Path(d)/"NOTICE").write_text("hello\n")
        (Path(d)/"CODEOWNERS").write_text("x\n")
        assert any("ABSENT" in x for x in audit(d, pins)), "creation of absent file must flag"
        (Path(d)/"CODEOWNERS").unlink()
        del pins["CODEOWNERS"]; pins["LICENSE"] = "0"*64
        assert any("MISSING" in x for x in audit(d, pins)), "missing pinned file must flag"
    print("sensitive-drift-audit selftest: PASS (4 cases)")
    return 0

def main():
    if "--selftest" in sys.argv:
        return selftest()
    pins = json.loads(os.environ.get("SENSITIVE_PINS", "{}"))
    if not pins:
        print("SENSITIVE_PINS empty — failing closed"); return 1
    drift = audit(".", pins)
    if drift:
        print("SENSITIVE DRIFT DETECTED:")
        print("\n".join(drift))
        if "--open-issue" in sys.argv and os.environ.get("GH_TOKEN"):
            open_issue(drift)
        return 1
    print(f"sensitive-drift-audit: OK ({len(pins)} paths pinned)")
    return 0

if __name__ == "__main__":
    sys.exit(main())

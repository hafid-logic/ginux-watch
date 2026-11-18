#!/usr/bin/env python3
"""auto-merge.py — v8.4-B: event-driven internal PR auto-merge (HDAE standing delegation).

Triggered by workflow_run(ci completed). Uses ONLY the built-in GITHUB_TOKEN.
Guards per config/authorization.yml: same-repo, open, non-draft, ci success,
mergeable_state clean, authz path decision (denylist protects the guardrails).
auto => merge (no force) + evidence comment + action-ledger entry [skip ci].
needs-owner => label + ONE deduped comment. Never touches upstream. Never closes PRs.
"""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import authz_check as az  # noqa: E402
MARKER = "<!-- v8.4-auto-merge -->"
REPO = os.environ.get("GITHUB_REPOSITORY", "hafid-logic/ginux-watch")

def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("gh %s failed: %s" % (args[:3], r.stderr[:200]))
    return r.stdout

def decide(pr, files, ci_conclusion, pol):
    """Pure decision function (offline-tested). Returns (verdict, reason)."""
    im = pol["internal_merge"]
    if pr.get("state") != "open":
        return ("skip", "not-open")
    if im.get("deny_draft") and pr.get("draft"):
        return ("skip", "draft")
    head_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name")
    base_repo = ((pr.get("base") or {}).get("repo") or {}).get("full_name")
    if im.get("same_repo_only") and head_repo != base_repo:
        return ("skip", "fork")
    if ci_conclusion != im["require_conclusion"]:
        return ("skip", "ci:" + str(ci_conclusion))
    if pr.get("mergeable_state") != im["require_mergeable_state"]:
        return ("skip", "mergeable:" + str(pr.get("mergeable_state")))
    return az.pr_files_decision(files, pol)

def already_commented(num, head_sha):
    try:
        comments = json.loads(gh("api", f"repos/{REPO}/issues/{num}/comments?per_page=100"))
    except Exception:
        return False
    return any(MARKER in (c.get("body") or "") and head_sha[:8] in (c.get("body") or "") for c in comments)

def comment(num, body):
    gh("api", "-X", "POST", f"repos/{REPO}/issues/{num}/comments", "-f", "body=" + body)

def ledger(entry):
    p = ROOT / "state/action-ledger.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        subprocess.run(["git", "add", "state/action-ledger.jsonl"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "state: action-ledger entry [skip ci]"], cwd=ROOT, check=True)
        for _ in range(3):
            r = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
            if r.returncode == 0:
                break
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=ROOT, capture_output=True)
    except Exception as e:
        print("ledger push best-effort failed:", e)

def main():
    ev = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    run = ev["workflow_run"]
    pol = az.load()
    nums = [p["number"] for p in run.get("pull_requests") or []]
    if not nums:
        prs = json.loads(gh("api", f"repos/{REPO}/pulls?state=open&per_page=100"))
        nums = [p["number"] for p in prs if p["head"]["sha"] == run["head_sha"]]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for num in nums:
        pr = json.loads(gh("api", f"repos/{REPO}/pulls/{num}"))
        files = [f["filename"] for f in json.loads(gh("api", f"repos/{REPO}/pulls/{num}/files?per_page=100"))]
        verdict, reason = decide(pr, files, run.get("conclusion"), pol)
        head = pr["head"]["sha"]
        print(f"PR #{num}: {verdict} ({reason})")
        if verdict == "auto":
            r = gh("api", "-X", "PUT", f"repos/{REPO}/pulls/{num}/merge", "-f", "merge_method=merge", check=False)
            merged = json.loads(r) if r.strip().startswith("{") else {}
            if merged.get("merged"):
                body = f"{MARKER} auto-merged under standing delegation (v8.4). head `{head[:8]}`, ci success, guards: {reason}. run {run.get('html_url','')}"
                comment(num, body)
                ledger({"at": now, "action": "internal_pr_merge", "pr": num, "head": head, "merge_sha": merged.get("sha"), "reason": reason})
                # GITHUB_TOKEN merges do not fire push events (anti-recursion);
                # repository_dispatch DOES trigger the watcher sweep (v8.4-E).
                gh("api", "-X", "POST", f"repos/{REPO}/dispatches", "-f", "event_type=sweep", check=False)
            else:
                print("merge refused:", str(merged)[:200])
        elif verdict == "needs-owner" and not already_commented(num, head):
            gh("label", "create", pol["internal_merge"]["needs_owner_label"], "--repo", REPO, check=False)
            gh("pr", "edit", str(num), "--repo", REPO, "--add-label", pol["internal_merge"]["needs_owner_label"], check=False)
            comment(num, f"{MARKER} head `{head[:8]}`: owner decision required — {reason}. Auto-merge withheld per config/authorization.yml.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

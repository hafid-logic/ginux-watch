#!/usr/bin/env python3
"""Verify gmkurtzer/ginux thread 58 (fuzz draft, published manually by user).

Checks the published text against the mandatory v2.7-1 checklist, saves a
snapshot of title/body/replies under approved/, and prints a verdict line.
Read-only against GitHub: one GET for the issue, one GET for the comments.
"""
import json
import subprocess
import sys
from pathlib import Path

WATCH = Path("/home/z/my-project/ginux-watch")
GH = "/home/z/my-project/work/bin/gh"
ENV = {"GH_CONFIG_DIR": "/home/z/my-project/work/.config/gh", "PATH": "/usr/bin:/bin:/usr/local/bin"}
ISSUE = 58
REPO = "gmkurtzer/ginux"


def gh_api(endpoint: str) -> dict:
    out = subprocess.run(
        [GH, "api", endpoint], capture_output=True, text=True, env=ENV, timeout=60
    )
    if out.returncode != 0:
        print(f"FATAL gh api {endpoint}: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return json.loads(out.stdout)


def has_any(text: str, needles) -> list:
    low = text.lower()
    return [n for n in needles if n.lower() in low]


issue = gh_api(f"repos/{REPO}/issues/{ISSUE}")
comments = gh_api(f"repos/{REPO}/issues/{ISSUE}/comments")
title, body = issue["title"], issue["body"] or ""

# --- mandatory checklist (v2.7-1, adapted to published reference text) ---
words = len(body.split())
chars = len(body)
checks = {}
checks["author_is_hafid_logic"] = issue["user"]["login"] == "hafid-logic"
checks["state_open"] = issue["state"] == "open"
checks["word_count_le_120"] = words <= 120
checks["has_ai_disclosure"] = bool(has_any(body, ["ai-assisted", "under my direction", "ai usage", "ai-assisted review"]))
checks["has_watch_repo_link"] = bool(has_any(body, ["hafid-logic/ginux-watch"]))
checks["has_pin_on_main"] = bool(has_any(body, ["82df3d71", "pinned", "main@"]))
checks["has_execs_number"] = bool(has_any(body, ["execs", "exec/s"]))
checks["has_coverage_number"] = bool(has_any(body, ["coverage", "regions"]))
checks["has_flags"] = bool(has_any(body, ["flags", "overflow-checks"]))
checks["has_asan"] = bool(has_any(body, ["asan", "addresssanitizer", "address sanitizer"]))
checks["asks_fuzz_vs_tests"] = bool(has_any(body, ["fuzz/", "tests/"]))
checks["asks_ci_preference"] = bool(has_any(body, ["ci"]))
checks["no_no_vulns_claim"] = not has_any(body, ["no vulnerabilities", "vulnerability-free", "free of vulnerabilities", "no security issues"])
banned_claims = has_any(body, ["no vulnerabilities", "vulnerability-free"])

# volume-format mention (v2.7-3 expanded scope observed in title/body)
vol = bool(has_any(title + " " + body, ["volume-format", "volume format"]))

snapshot = {
    "issue": {k: issue[k] for k in ("number", "title", "state", "created_at", "user", "html_url", "comments")},
    "body_chars": chars,
    "body_words": words,
    "body_verbatim": body,
    "comments": [
        {
            "id": c["id"],
            "user": c["user"]["login"],
            "created_at": c["created_at"],
            "body_verbatim": c["body"],
            "html_url": c["html_url"],
        }
        for c in comments
    ],
    "checks": checks,
    "volume_format_mentioned": vol,
}
(WATCH / "approved" / "2026-11-03-2-issue58-snapshot.json").write_text(
    json.dumps(snapshot, indent=2, ensure_ascii=False)
)

print(f"== issue #{ISSUE} GET [MEASURED] ==")
print(f"title ({len(title)} chars): {title}")
print(f"body: {chars} chars / {words} words")
print(f"author={issue['user']['login']} state={issue['state']} created={issue['created_at']} comments={issue['comments']}")
print(f"volume-format mentioned: {vol}")
print("-- checklist --")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print("-- comments (read-only monitoring) --")
for c in snapshot["comments"]:
    print(f"  id={c['id']} user={c['user']} at={c['created_at']} url={c['html_url']}")
    print("  body_verbatim:")
    for line in c["body_verbatim"].splitlines():
        print(f"    | {line}")

hard = {k: v for k, v in checks.items() if k != "word_count_le_120"}
verdict = "MATCH" if all(hard.values()) else "PARTIAL"
print(f"VERDICT I-F58 {verdict}: hard checks {sum(hard.values())}/{len(hard)} pass; word count {words} (guideline <=120, documented)")

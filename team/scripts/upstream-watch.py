#!/usr/bin/env python3
"""Upstream parser-crate watch (v3.2 §2).

Compares current upstream main with matrix/upstream-watch.json; if any commit
range touched a parser crate, dispatches a short fuzz round (repository_dispatch
"fuzz-round", seconds=600) on this repository, then updates the state file.

Parser crates (v3.2): crates/oci, protocol-state, volume-format + the
parser-adjacent crates/image-store, oci-cache, display-protocol (decode(&[u8])).

Fail-safe: the compare API caps the file list (300 files); when the list is
truncated we treat parser_touched=True — a wave that big almost certainly
touched parsers, and a short 10-minute round is the cheap direction to err into.
"""
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote

WATCH_REPO = os.environ.get("GITHUB_REPOSITORY", "hafid-logic/ginux-watch")
STATE = pathlib.Path("matrix/upstream-watch.json")
UPSTREAM = "gmkurtzer/ginux"
PARSER_PREFIXES = (
    "crates/oci/",
    "crates/protocol-state/",
    "crates/volume-format/",
    "crates/image-store/",
    "crates/oci-cache/",
    "crates/display-protocol/",
)

# Disabled 2026-11-05 (v3.6 §2a — archive/light-monitoring phase): no fuzz rounds are
# dispatched on parser-crate merges while upstream ginux is in archive/userspace pivot.
# Re-enable: set to True (docs/RECOVERY.md §8). Comparison/state updates still run.
DISPATCH_FUZZ_ROUND = False

# v6.3-3: watched upstream threads (read-only, internal GITHUB_TOKEN).
# threads 222 (overflow-checks issue), 207 (pollfd PR), 227 (our restore-overflow-checks PR).
# PRs are issues in the REST API, so /issues/{n} covers both kinds.
THREADS = (222, 207, 227)


def watch_threads(state, now, out) -> None:
    """Record thread state (open/closed/merged), last state change, comments.

    Read-only against the public upstream repo; never posts, never reacts
    (fixed rules). Snapshot lands in matrix/upstream-watch.json under
    "threads_watch"; deltas vs the previous snapshot are reported in `out`
    (and thus in the workflow commit summary). Runs on EVERY sweep,
    including unchanged-head and first-run paths.

    v7.7-1: a thread STATE TRANSITION (open->closed/merged) is a first-class
    watch-breaker trigger, emitted as its own "STATE-TRANSITION" line — same
    severity as a new comment. "merged" comes from /pulls/{n} (issues only
    know open/closed); "state_changed_at" records when the transition happened
    (merged_at, else closed_at).
    """
    prev = state.get("threads_watch", {})
    snap = {}
    for n in THREADS:
        try:
            issue = json.loads(gh("api", f"repos/{UPSTREAM}/issues/{n}"))
            comments = json.loads(
                gh("api", f"repos/{UPSTREAM}/issues/{n}/comments?per_page=100")
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            out.append(f"threads_watch #{n}: api error (kept previous snapshot)")
            snap[str(n)] = prev.get(str(n), {"api_error": True, "checked": now})
            continue
        last = comments[-1] if comments else None
        # v7.7-1: PR threads also report merged + when the state changed.
        pull = None
        if issue.get("pull_request"):
            try:
                pull = json.loads(gh("api", f"repos/{UPSTREAM}/pulls/{n}"))
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                pull = None
        merged = bool(pull and pull.get("merged"))
        tstate = "merged" if merged else issue.get("state")
        state_changed_at = (pull or {}).get("merged_at") if merged \
            else issue.get("closed_at")
        snap[str(n)] = {
            "state": tstate,
            "state_changed_at": state_changed_at,
            "comments": issue.get("comments"),
            "updated_at": issue.get("updated_at"),
            "last_comment_at": last.get("created_at") if last else None,
            "last_comment_author": (last.get("user") or {}).get("login") if last else None,
            "checked": now,
        }
    state["threads_watch"] = snap
    for n in THREADS:
        cur, old = snap.get(str(n)), prev.get(str(n))
        if cur is None:
            continue
        if old is None:
            out.append(
                f"threads_watch #{n} baseline: comments={cur.get('comments')} "
                f"last={cur.get('last_comment_at')} state={cur.get('state')}"
            )
        elif (
            cur.get("comments") != old.get("comments")
            or cur.get("last_comment_at") != old.get("last_comment_at")
            or cur.get("state") != old.get("state")
        ):
            if cur.get("state") != old.get("state"):
                out.append(
                    f"threads_watch #{n} STATE-TRANSITION: {old.get('state')}->"
                    f"{cur.get('state')} at {cur.get('state_changed_at')} — "
                    "watch-breaker trigger (v7.7-1, same severity as a comment)"
                )
            out.append(
                f"threads_watch #{n} CHANGED: comments {old.get('comments')}->"
                f"{cur.get('comments')} last={cur.get('last_comment_at')} "
                f"state {old.get('state')}->{cur.get('state')}"
            )


def gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def main() -> int:
    state = {"last_seen_sha": None, "last_checked": None, "last_dispatch": None}
    if STATE.exists():
        state.update(json.loads(STATE.read_text(encoding="utf-8")))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # v7.2-2: heartbeat (آخر تشغيل) + عتبة الإنذار 12 ساعة — جدولة Actions best-effort.
    # v7.3-2d: last_run/last_success/last_conclusion منفصلة؛ الإنذار يستند إلى
    # last_success (heartbeat_check.py). اكتمال هذه الجولة وحده يقدّم last_success؛
    # فشل لاحق في نفس الـrun يصحّحه heartbeat-finalize.py (if: failure()) الذي لا
    # يلمس last_success أبدًا — فشل التشغيل لا يُحسب نبضًا سليمًا.
    # دمج وليس استبدال: مفاتيح last_success/last_conclusion القائمة تُحفظ.
    hb = state.setdefault("heartbeat", {})
    hb["last_run"] = now
    hb["last_conclusion"] = "success"
    hb["last_success"] = now
    hb["alert_basis"] = "last_success"
    hb["source"] = "team-watcher (GitHub Actions)"
    hb["scheduling"] = "best-effort"
    state["alert_threshold_hours"] = 12
    head = json.loads(gh("api", f"repos/{UPSTREAM}/commits/main"))["sha"]
    last = state.get("last_seen_sha")
    out = [f"upstream main: last={str(last)[:8]} new={head[:8]}"]
    watch_threads(state, now, out)

    if not last:
        state.update({"last_seen_sha": head, "last_checked": now})
        STATE.write_text(json.dumps(state, indent=1) + "\n")
        out.append("first run: baseline recorded, no dispatch")
        print("\n".join(out))
        return 0

    if head == last:
        state["last_checked"] = now
        STATE.write_text(json.dumps(state, indent=1) + "\n")
        out.append("unchanged")
        print("\n".join(out))
        return 0

    cmp = json.loads(
        gh("api", f"repos/{UPSTREAM}/compare/{quote(last)}...{quote(head)}")
    )
    files = [f["filename"] for f in cmp.get("files", [])]
    truncated = cmp.get("files", []) and len(files) >= 300
    touched = sorted({f for f in files if f.startswith(PARSER_PREFIXES)})
    parser_touched = bool(touched) or bool(truncated)
    out.append(
        f"commits={cmp.get('total_commits')} files={len(files)} "
        f"truncated={truncated} parser_touched={parser_touched}"
    )
    if touched:
        out += [f"  {p}" for p in touched[:12]]

    if parser_touched and DISPATCH_FUZZ_ROUND:
        gh(
            "api",
            "-X",
            "POST",
            f"repos/{WATCH_REPO}/dispatches",
            "-f",
            "event_type=fuzz-round",
            "-f",
            "client_payload[seconds]=600",
            "-f",
            f"client_payload[reason]=parser-crate-touched {last[:8]}..{head[:8]}",
        )
        state["last_dispatch"] = {
            "at": now,
            "range": f"{last[:8]}..{head[:8]}",
            "files": touched[:12],
            "truncated": truncated,
        }
        out.append("dispatched: fuzz-round seconds=600")
    else:
        out.append("no parser crates touched: no dispatch")

    state.update({"last_seen_sha": head, "last_checked": now})
    STATE.write_text(json.dumps(state, indent=1) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write("### upstream parser watch\n```\n" + "\n".join(out) + "\n```\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

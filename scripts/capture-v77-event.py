#!/usr/bin/env python3
"""capture-v77-event.py — v7.7 clause 0: record the 2026-11-13 thread-closure
event into the watch baseline (matrix/upstream-watch.json).

Data source: live anonymous GitHub REST API captured this session (raw JSON
kept session-local under work/results/v77-*.json; the verbatim owner comments
land in inbox/2026-11-13-threads-closed-222-207-227-gmkurtzer.md inside
UNTRUSTED blocks). This script only writes DATA — it never posts, never
reacts (fixed rules), and never touches any secret.

Baseline updates:
  threads_watch[222] closed     @2026-11-13T02:27:17Z (comments 2 -> 4)
  threads_watch[207] closed     @2026-11-13T02:58:34Z (comments 4 -> 5; NOT merged —
                                head b19e3ea3 is not an ancestor of upstream/main)
  threads_watch[227] merged     @2026-11-13T02:27:02Z (merge commit 0c290040)
  breaker_absorbed += 222/207/227 entries pointing at the inbox capture.

Idempotent: re-running rewrites the same values (checked timestamp only moves).
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

STATE = pathlib.Path("matrix/upstream-watch.json")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
CAPTURED_IN = "inbox/2026-11-13-threads-closed-222-207-227-gmkurtzer.md"
HEADS = {
    "upstream_main": "49b42307",
    "pr207_head": "b19e3ea3 (closed unmerged — not an ancestor of upstream/main)",
    "pr227_head": "31f82869 (repaired head merged via 0c290040)",
}
EVENTS = {
    "222": {
        "state": "closed", "state_changed_at": "2026-11-13T02:27:17Z",
        "comments": 4, "updated_at": "2026-11-13T02:27:17Z",
        "last_comment_at": "2026-11-13T02:27:13Z", "last_comment_author": "gmkurtzer",
    },
    "207": {
        "state": "closed", "state_changed_at": "2026-11-13T02:58:34Z",
        "comments": 5, "updated_at": "2026-11-13T02:58:34Z",
        "last_comment_at": "2026-11-13T02:58:33Z", "last_comment_author": "gmkurtzer",
    },
    "227": {
        "state": "merged", "state_changed_at": "2026-11-13T02:27:02Z",
        "comments": 1, "updated_at": "2026-11-13T02:27:02Z",
        "last_comment_at": "2026-11-06T14:58:30Z", "last_comment_author": "gmkurtzer",
    },
}


def absorbed(n):
    return {
        "event": {
            "222": "gmkurtzer recheck (01:36:28Z) + resolved-and-merged note (02:27:13Z); issue closed 02:27:17Z",
            "207": "gmkurtzer closing comment 02:58:33Z — closed unmerged with structural reason (PTRACE_PEEKDATA snapshot vs live pollfd)",
            "227": "PR merged by owner 02:27:02Z after repair branch codex/repair-pr-227 (4b8d4d53) + CI wiring commit 31f82869",
        }[n],
        "first_detected": "2026-11-13T10:52Z (session v7.7 — fetch + ls-remote + anonymous API)",
        "absorbed_at": "%s (session v7.7, clause 0)" % NOW,
        "captured_in": CAPTURED_IN,
        "verbatim_capture": "owner comments saved verbatim in UNTRUSTED blocks; raw API JSON session-local work/results/v77-*.json",
        "heads_at_capture": HEADS,
        "status": "known — breaker back to ok; no reply, no reaction (fixed rules)",
    }


def main() -> int:
    if not STATE.exists():
        print("missing %s" % STATE, file=sys.stderr)
        return 2
    state = json.loads(STATE.read_text(encoding="utf-8"))
    prev = state.get("threads_watch", {})
    snap = {}
    for n, ev in EVENTS.items():
        snap[n] = dict(ev, checked=NOW)
    state["threads_watch"] = snap
    ba = state.setdefault("breaker_absorbed", {})
    for n in EVENTS:
        ba[n] = absorbed(n)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    for n in EVENTS:
        old = prev.get(n, {})
        print("threads_watch #%s: state %s->%s comments %s->%s changed_at=%s" % (
            n, old.get("state"), snap[n]["state"], old.get("comments"),
            snap[n]["comments"], snap[n]["state_changed_at"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

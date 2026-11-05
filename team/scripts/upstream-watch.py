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


def gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def main() -> int:
    state = {"last_seen_sha": None, "last_checked": None, "last_dispatch": None}
    if STATE.exists():
        state.update(json.loads(STATE.read_text(encoding="utf-8")))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = json.loads(gh("api", f"repos/{UPSTREAM}/commits/main"))["sha"]
    last = state.get("last_seen_sha")
    out = [f"upstream main: last={str(last)[:8]} new={head[:8]}"]

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

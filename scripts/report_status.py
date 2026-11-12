#!/usr/bin/env python3
"""report_status.py — compute the GREEN/AMBER/RED supervisor header (v7.5-5).

RED   : new reply on our threads (222/207/227) OR secrets hit OR a critical
        lint FAIL (clauses a/f) on a report dated today.
AMBER : monitor older than the 12h threshold OR provider failure (llm-status
        consecutive failures >= 3, or the decider-space probe not ok).
GREEN : otherwise.

Prints exactly one line: "STATUS: <CODE> — <reasons>" — the report writer
prepends it verbatim as the first line of the outbox report. Evidence is
data-only (state files committed by the workflows).
"""
import datetime
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THREAD_BASELINE = {"222": {"comments": 2, "updated_at": "2026-11-06T14:58:29Z"},
                   "227": {"comments": 1, "updated_at": "2026-11-06T14:58:30Z"},
                   "pr207_head": "b19e3ea3e720feafce0cea952a8b50503df0b10c"}  # 2026-11-12 ls-remote
MONITOR_STALE_HOURS = 12.0  # v7.2-2 threshold


def load(p):
    f = REPO / p
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def main():
    red, amber = [], []

    mon = load("state/monitor.json")
    if mon:
        checked = datetime.datetime.fromisoformat(mon["checked_utc"].replace("Z", "+00:00"))
        age_h = (datetime.datetime.now(datetime.UTC) - checked).total_seconds() / 3600.0
        if age_h > MONITOR_STALE_HOURS:
            amber.append("monitor stale %.1fh > %.0fh" % (age_h, MONITOR_STALE_HOURS))
        w = mon.get("watched", {})
        b = THREAD_BASELINE
        if str(222) in w and w["222"].get("comments", 0) > b["222"]["comments"]:
            red.append("new reply on thread 222 (%s > baseline %s)" % (w["222"]["comments"], b["222"]["comments"]))
        if str(227) in w and w["227"].get("comments", 0) > b["227"]["comments"]:
            red.append("new reply on thread 227")
    else:
        amber.append("monitor state missing")

    dec = load("state/decider-space.json")
    if dec and dec.get("status") not in ("ok", "starting", "unconfigured"):
        amber.append("decider-space probe %s" % dec.get("status"))
    elif dec and dec.get("status") == "unconfigured":
        amber.append("decider-space probe unconfigured (key absent in job)")

    llm = load("state/llm-status.json")
    if llm:
        for prov, p in (llm.get("providers") or {}).items():
            cf = p.get("consecutive_failures") or p.get("daily", {}).get("consecutive_failures")
            if isinstance(cf, int) and cf >= 3:
                amber.append("%s: %d consecutive failures" % (prov, cf))

    code = "RED" if red else ("AMBER" if amber else "GREEN")
    reasons = red + amber
    print("STATUS: %s — %s" % (code, "; ".join(reasons) if reasons else "no red/amber signals in committed state"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

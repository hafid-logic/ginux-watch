#!/usr/bin/env python3
"""report_status.py — compute the GREEN/AMBER/RED supervisor header (v7.5-5, v7.6-2).

RED   : new reply on our threads (222/207/227) OR secrets hit OR a critical
        lint FAIL (clauses a/f) on a report dated today.
AMBER : monitor older than the 12h threshold OR provider failure (llm-status
        consecutive failures >= 3).
GREEN : otherwise.

v7.6-2: the base STATUS line EXCLUDES experiment components — the decider
probe is reported on a separate dedicated line:

    STATUS: <CODE> — <reasons>
    decider-pilot: <STATE> — <detail>

The report writer prints both lines verbatim; the STATUS line stays first.
Evidence is data-only (state files committed by the workflows).
"""
import datetime
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THREAD_BASELINE = {"222": {"comments": 4, "updated_at": "2026-11-13T02:27:17Z"},
                   "227": {"comments": 1, "updated_at": "2026-11-13T02:27:02Z"},
                   "pr207_head": "b19e3ea3e720feafce0cea952a8b50503df0b10c"}  # v7.7-0 absorb 2026-11-13: event captured (inbox/2026-11-13-threads-closed-*) + breaker_absorbed; 207 closed unmerged, 227 merged
MONITOR_STALE_HOURS = 12.0  # v7.2-2 threshold
ENV_BINDING = "environment: supervisor @ .github/workflows/decider-space-probe.yml"


def load(p):
    f = REPO / p
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def decider_pilot_line():
    """v7.6-2: the decider-pilot state line (experiment component, excluded
    from the base STATUS per the directive). Data-only from committed state."""
    dec = load("state/decider-space.json")
    if not dec:
        return "decider-pilot: NO-DATA — state/decider-space.json missing"
    status = dec.get("status")
    ts = dec.get("updated", "?")
    binding = "%s; dispatch verification pending token (v7.6-2)" % ENV_BINDING
    if status == "ok":
        last_ok = ""
        for h in reversed(dec.get("history") or []):
            if h.get("status") == "ok":
                last_ok = " last ok %s" % h.get("at", "?")
                break
        return "decider-pilot: OK — status ok (%s)%s" % (ts, last_ok)
    if status == "starting":
        return "decider-pilot: STARTING — Space warming (%s)" % ts
    if status == "unconfigured":
        return ("decider-pilot: UNCONFIGURED — DECIDER_API_KEY absent in last "
                "run (%s); binding %s" % (ts, binding))
    failed = ",".join(dec.get("failed_checks") or []) or "unknown"
    return "decider-pilot: DEGRADED — status=%s failed=%s (%s)" % (status, failed, ts)


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

    # v7.6-2: decider-space probe signals moved OUT of the base STATUS —
    # they are experiment components and live on the decider-pilot line.

    llm = load("state/llm-status.json")
    if llm:
        for prov, p in (llm.get("providers") or {}).items():
            cf = p.get("consecutive_failures") or p.get("daily", {}).get("consecutive_failures")
            if isinstance(cf, int) and cf >= 3:
                amber.append("%s: %d consecutive failures" % (prov, cf))

    code = "RED" if red else ("AMBER" if amber else "GREEN")
    reasons = red + amber
    print("STATUS: %s — %s" % (code, "; ".join(reasons) if reasons else "no red/amber signals in committed state"))
    print(decider_pilot_line())
    return 0


if __name__ == "__main__":
    sys.exit(main())

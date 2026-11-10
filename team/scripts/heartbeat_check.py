#!/usr/bin/env python3
"""heartbeat-check.py — v7.3-2d offline alert evaluation for the team-watcher
heartbeat (matrix/upstream-watch.json).

Policy (v7.3-2d):
  - the alert basis is last_success (NOT last_run): a failed run is NOT a
    healthy pulse and must not reset the staleness timer;
  - threshold: alert_threshold_hours (12) counted since the last SUCCESSFUL
    run; a fresh failed run does not silence the alert;
  - last_run / last_conclusion are diagnostics only.

evaluate_heartbeat(hb, now) is pure and offline; the CLI reads the matrix
file and prints the verdict JSON (exit 0 always — agent-side diagnostic,
not a CI gate). Tested by team/scripts/test-heartbeat-check.py."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def evaluate_heartbeat(hb, now):
    """Pure decision: given the heartbeat object and a tz-aware 'now', return
    {alert, basis, stale_hours, threshold_hours, reason}."""
    basis = hb.get("alert_basis", "last_success")
    threshold = float(hb.get("alert_threshold_hours", 12))
    ls = hb.get("last_success")
    if not ls:
        return {"alert": True, "basis": basis, "stale_hours": None,
                "threshold_hours": threshold,
                "reason": "no last_success recorded — never a healthy pulse yet"}
    stale = (now - _parse(ls)).total_seconds() / 3600.0
    concl = hb.get("last_conclusion")
    note = ""
    if concl and concl != "success":
        note = " (last run %s=%s — a failed run does not refresh the pulse)" % (
            hb.get("last_run"), concl)
    if stale > threshold:
        return {"alert": True, "basis": basis, "stale_hours": round(stale, 2),
                "threshold_hours": threshold,
                "reason": "last_success %s is %.2fh old > %.1fh threshold%s" % (
                    ls, stale, threshold, note)}
    return {"alert": False, "basis": basis, "stale_hours": round(stale, 2),
            "threshold_hours": threshold,
            "reason": "healthy: last_success %s is %.2fh old <= %.1fh threshold%s" % (
                ls, stale, threshold, note)}


def main():
    p = Path(sys.argv[1] if len(sys.argv) > 1 else "matrix/upstream-watch.json")
    hb = json.loads(p.read_text(encoding="utf-8")).get("heartbeat", {})
    now = datetime.now(timezone.utc)
    for a in sys.argv[2:]:
        if a.startswith("--now="):
            now = _parse(a.split("=", 1)[1])
    print(json.dumps(evaluate_heartbeat(hb, now), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

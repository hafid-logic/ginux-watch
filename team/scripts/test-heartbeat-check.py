#!/usr/bin/env python3
"""test-heartbeat-check.py — v7.3-2d offline test for the heartbeat alert
semantics. NO network, NO provider calls, NO GitHub API.
Asserts: alert basis = last_success; the 12h threshold boundary; a FAILED
run does NOT count as a healthy heartbeat (stale success + fresh failed run
=> alert stands); a successful run refreshes last_success and clears."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heartbeat_check import evaluate_heartbeat  # noqa: E402

NOW = datetime(2026, 11, 10, 5, 0, 0, tzinfo=timezone.utc)


def hb(last_success=None, last_run=None, conclusion="success", threshold=12):
    d = {"alert_basis": "last_success", "alert_threshold_hours": threshold}
    if last_success:
        d["last_success"] = last_success
    if last_run:
        d["last_run"] = last_run
    d["last_conclusion"] = conclusion
    return d


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


CASES = [
    # (name, heartbeat, expected_alert)
    ("fresh success 5h ago -> no alert",
     hb(iso(NOW - timedelta(hours=5)), iso(NOW - timedelta(hours=5))), False),
    ("success 11.9h ago -> no alert (boundary inside)",
     hb(iso(NOW - timedelta(hours=11.9)), iso(NOW - timedelta(hours=11.9))), False),
    ("success 12.5h ago -> alert (boundary crossed)",
     hb(iso(NOW - timedelta(hours=12.5)), iso(NOW - timedelta(hours=0.5))), True),
    ("FAILED fresh run + stale success 14h -> ALERT (failed run is not a pulse)",
     hb(iso(NOW - timedelta(hours=14)), iso(NOW - timedelta(hours=1)), "failure"), True),
    ("FAILED fresh run + success 5h ago -> no alert (success still fresh)",
     hb(iso(NOW - timedelta(hours=5)), iso(NOW - timedelta(hours=1)), "failure"), False),
    ("no last_success at all -> alert",
     {"alert_basis": "last_success", "alert_threshold_hours": 12,
      "last_run": iso(NOW - timedelta(hours=1)), "last_conclusion": "failure"}, True),
    ("missing last_success field only with fresh failure -> alert",
     {"alert_basis": "last_success", "alert_threshold_hours": 12,
      "last_run": iso(NOW), "last_conclusion": "failure"}, True),
]

fails = 0
for name, d, expected in CASES:
    got = evaluate_heartbeat(d, NOW)["alert"]
    ok = got == expected
    fails += 0 if ok else 1
    print(("PASS" if ok else "FAIL"), "-", name, "-> alert:", got)

if fails:
    print("test-heartbeat-check: %d/%d FAILED" % (fails, len(CASES)))
    sys.exit(1)
print("test-heartbeat-check: %d/%d PASS (offline, no network)" % (len(CASES), len(CASES)))

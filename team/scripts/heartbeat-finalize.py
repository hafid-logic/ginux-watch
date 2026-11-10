#!/usr/bin/env python3
"""heartbeat-finalize.py — team-watcher run-level heartbeat record (v7.3-2d).

Runs as the LAST team-watcher step with if: failure(): a FAILED run must not
count as a healthy heartbeat. Writes last_conclusion from the actual job
status and refreshes last_run; it NEVER advances last_success (that advance
belongs to a successful run only — upstream-watch.py writes last_success on
sweep completion, and the regular commit step propagates it; when the job
fails that write is never committed, so the world never sees a false pulse).

Commits the matrix update with [skip ci] and a 3-attempt rebase+push retry,
because the regular commit step is skipped when the job failed. Best-effort:
never masks the original failure (exit 0 even if the push retry exhausts).
Decision semantics are offline-tested in heartbeat_check.py /
test-heartbeat-check.py."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE = Path("matrix/upstream-watch.json")


def run(cmd, **kw):
    return subprocess.run(cmd, **kw)


def main():
    status = os.environ.get("JOB_STATUS", "failure")
    data = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    hb = data.setdefault("heartbeat", {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    hb["last_run"] = now
    hb["last_conclusion"] = status
    hb["alert_basis"] = "last_success"   # basis unchanged: alert reads last_success
    hb.setdefault("source", "team-watcher (GitHub Actions)")
    hb["scheduling"] = "best-effort"
    hb["checked"] = now
    data["alert_threshold_hours"] = int(data.get("alert_threshold_hours", 12))
    STATE.write_text(json.dumps(data, indent=1) + "\n")

    run(["git", "config", "user.name", "team-watcher"], check=True)
    run(["git", "config", "user.email", "actions@users.noreply.github.com"], check=True)
    run(["git", "add", str(STATE)], check=True)
    if run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("heartbeat: no change to record")
        return 0
    msg = "heartbeat %s [skip ci]" % status
    for i in (1, 2, 3):
        if run(["git", "commit", "-m", msg]).returncode == 0 \
                and run(["git", "pull", "--rebase", "origin", "main"]).returncode == 0 \
                and run(["git", "push", "origin", "HEAD:main"]).returncode == 0:
            print("heartbeat: recorded (%s)" % status)
            return 0
        run(["sleep", str(i * 5)])
    sys.stderr.write("heartbeat: push failed after 3 attempts (best-effort)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

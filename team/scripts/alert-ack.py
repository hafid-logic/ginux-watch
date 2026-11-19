#!/usr/bin/env python3
"""alert-ack.py — v8.4-C: repeat-until-acknowledged attention loop (HDAE pr-issue-review).

Tracks OUR repo's open TRIPPED issues; reminds the owner until acknowledged
(label 'acknowledged' or an owner comment containing ACK / اقرار). INTERNAL only —
never nags upstream (band 14 preserved). Reminders at most once per 6h, deduped.
Pure core acknowledged()/reminder_due() is offline-tested. Uses gh + GITHUB_TOKEN.
"""
import argparse, json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import action_ledger as led  # noqa: E402
REPO = os.environ.get("GITHUB_REPOSITORY", "hafid-logic/ginux-watch")
OWNER = REPO.split("/")[0]
STATE = ROOT / "state/alerts.json"
MARKER = "<!-- v8.4-alert-ack -->"

def acknowledged(labels, comments, owner=OWNER):
    if any((l.get("name") or "").lower() == "acknowledged" for l in labels or []):
        return True
    for c in comments or []:
        if ((c.get("user") or {}).get("login") == owner):
            body = (c.get("body") or "")
            if re.search(r"\back\b", body, re.I) or "اقرار" in body or "إقرار" in body:
                return True
    return False

def reminder_due(first_seen, last_reminder, ack, now_iso, max_hours=48):
    """v8.7: ONE reminder per item; stop at first ACK or after 48h."""
    if ack: return False
    if last_reminder: return False
    if not first_seen: return True
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        fs = datetime.strptime(first_seen, fmt); now = datetime.strptime(now_iso, fmt)
    except ValueError:
        return True
    return (now - fs).total_seconds() <= max_hours * 3600

def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("gh failed: %s" % r.stderr[:150])
    return r.stdout

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save(d):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mark-ack", type=int)
    a = ap.parse_args()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = load()
    if a.mark_ack:
        e = data.get(str(a.mark_ack), {}); e["ack"] = True; e["ack_at"] = now
        data[str(a.mark_ack)] = e; save(data)
        led.record({"at": now, "action": "alert_ack", "target": a.mark_ack})
        print("acknowledged #%s" % a.mark_ack); return 0
    issues = json.loads(gh("issue", "list", "--repo", REPO, "--state", "open", "--limit", "200",
                           "--json", "number,title,labels"))
    for it in issues:
        if not it["title"].startswith("TRIPPED:"):
            continue
        n = str(it["number"]); e = data.get(n, {"first_seen": now})
        comments = json.loads(gh("api", f"repos/{REPO}/issues/{n}/comments?per_page=100"))
        if acknowledged(it.get("labels"), comments):
            if not e.get("ack"):
                e["ack"] = True; e["ack_at"] = now
                led.record({"at": now, "action": "alert_ack", "target": n})
        else:
            e["ack"] = False
            if reminder_due(e.get("first_seen"), e.get("last_reminder"), e.get("ack"), now):
                body = f"{MARKER} reminder: outstanding alert awaiting owner acknowledgment (label `acknowledged` or comment ACK / اقرار). Internal attention only."
                gh("issue", "comment", n, "--repo", REPO, "--body", body)
                e["last_reminder"] = now
                led.record({"at": now, "action": "alert_reminder", "target": n})
        data[n] = e
    save(data)
    print("alert-ack sweep done: %d tracked" % len(data))
    return 0

if __name__ == "__main__":
    sys.exit(main())

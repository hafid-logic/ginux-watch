#!/usr/bin/env python3
"""lease-sweep.py — watcher: enforce card leases (PROTOCOL.md §Claiming).

Expired claimed cards: git mv to team/tasks/stale/ (record), then re-queue a copy in
team/tasks/open/ (status: open, claim_until cleared, attempts+1). attempts would exceed 2 →
flag supervisor-review: yes and leave in stale/ without requeue. Prints a summary; the
calling workflow commits and pushes.
"""
import os, re, glob, shutil, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS = os.path.join(ROOT, "team", "tasks")
NOW = datetime.datetime.now(datetime.UTC)
MAX_ATTEMPTS = 2

def fm_field(text, key):
    m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""

def parse_iso(s):
    s = s.strip().replace("Z", "+00:00")
    try:
        return datetime.datetime.fromisoformat(s)
    except ValueError:
        return None

moved = []
for card in sorted(glob.glob(os.path.join(TASKS, "claimed", "T-*.md"))):
    txt = open(card, encoding="utf-8").read()
    cu = parse_iso(fm_field(txt, "claim_until") or "")
    if cu is None:
        continue
    if cu > NOW:
        continue
    base = os.path.basename(card)
    tid = fm_field(txt, "id") or base[:-3]
    try:
        attempts = int(fm_field(txt, "attempts") or "0")
    except ValueError:
        attempts = 0
    new_attempts = attempts + 1
    stale = os.path.join(TASKS, "stale", base)
    shutil.move(card, stale)
    moved.append(f"{tid}: expired -> stale (attempt {new_attempts})")
    txt2 = txt.replace("status: claimed", "status: stale", 1)
    txt2 = re.sub(r"^attempts:\s*\d+\s*$", f"attempts: {new_attempts}", txt2, count=1, flags=re.M)
    if new_attempts > MAX_ATTEMPTS:
        if "supervisor-review:" not in txt2:
            txt2 += "\nsupervisor-review: yes (attempts exceeded)\n"
        open(stale, "w", encoding="utf-8").write(txt2)
        moved.append(f"{tid}: attempts>{MAX_ATTEMPTS} flagged for supervisor, NOT requeued")
    else:
        stamp = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
        txt3 = txt2.replace("status: stale", "status: open", 1)
        txt3 = re.sub(r"^claim_until:.*$", "claim_until:", txt3, count=1, flags=re.M)
        txt3 += f"requeued_from: stale {stamp}\n"
        open(os.path.join(TASKS, "open", base), "w", encoding="utf-8").write(txt3)
        moved.append(f"{tid}: requeued to open")

print("\n".join(moved) if moved else "no expired leases")

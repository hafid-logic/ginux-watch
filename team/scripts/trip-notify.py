#!/usr/bin/env python3
"""TRIPPED notify (directive v6.5b-3): open an issue in hafid-logic/ginux-watch when a
watched thread (#222/#207/PR#227) changes (comment count / last stamp / state / PR head).
Dedup via fingerprints in matrix/notify-state.json. Simulate mode (workflow_dispatch input
simulate=true, or matrix/.simulate-flag): open a test issue, close it, record its number.
Never quotes upstream comment text: numbers + links only (<= 10 body lines)."""
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = "hafid-logic/ginux-watch"
MATRIX = Path("matrix/upstream-watch.json")
STATE = Path("matrix/notify-state.json")
FLAG = Path("matrix/.simulate-flag")
THREADS = {
    "222": "https://github.com/gmkurtzer/ginux/issues/222",
    "207": "https://github.com/gmkurtzer/ginux/issues/207",
    "227": "https://github.com/gmkurtzer/ginux/pull/227",
}
LABELS = ["state", "comments", "last_comment_at", "head227"]


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        class _R:
            returncode = 127
            stdout = ""
            stderr = "binary not found: %s" % cmd[0]
        return _R()


def gh(*args):
    r = run(["gh", *args])
    if r.returncode != 0:
        print("gh warn:", ((r.stderr or r.stdout) or "").strip()[:300], flush=True)
    return r


def pr227_head():
    r = run(["git", "ls-remote", "https://github.com/gmkurtzer/ginux.git",
             "refs/pull/227/head"])
    m = re.match(r"([0-9a-f]{40})\s+refs/pull/227/head", r.stdout.strip())
    return m.group(1) if m else "unknown"


def load_state():
    try:
        st = json.loads(STATE.read_text())
        if not isinstance(st.get("fingerprints"), dict):
            st["fingerprints"] = {}
        return st
    except Exception:
        return {"version": 1, "fingerprints": {}, "simulate_last_issue": None}


def fp_of(t, d, head):
    return {
        "state": d.get("state", "unknown"),
        "comments": d.get("comments"),
        "last_comment_at": d.get("last_comment_at"),
        "head227": head if t == "227" else None,
    }


def open_issue(title, body):
    r = gh("issue", "create", "--repo", REPO, "--title", title, "--body", body)
    m = re.search(r"/issues/(\d+)", r.stdout or "")
    return int(m.group(1)) if m else None


def main():
    simulate = os.environ.get("SIMULATE", "").strip().lower() == "true" or FLAG.exists()
    try:
        new = json.loads(MATRIX.read_text())
        threads = new.get("threads_watch", {})
    except Exception as e:
        print("trip-notify: no usable matrix:", e, flush=True)
        return
    state = load_state()
    head = pr227_head()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if simulate:
        body = "\n".join([
            "بطاقة اختبار آلي للإشعار (توجيه v6.5b-3 بند 3) — لا تغيير حقيقي في الخيوط المراقبة.",
            "المصدر: team-watcher في وضع simulate (workflow_dispatch بمدخل simulate=true، أو matrix/.simulate-flag).",
            "الخيوط المراقبة (روابط فقط):",
            THREADS["222"],
            THREADS["207"],
            THREADS["227"],
            "يُغلق هذا الـissue تلقائيًا بعد الفتح، ورقمه يُسجَّل في matrix/notify-state.json.",
        ])
        num = open_issue("TRIPPED: simulate-test", body)
        if num:
            gh("issue", "close", str(num), "--repo", REPO,
               "--comment", "simulate test — closed automatically (v6.5b-3)")
            print("SIMULATE_ISSUE=%d" % num, flush=True)
        else:
            print("SIMULATE_ISSUE=unknown", flush=True)
        state["simulate_last_issue"] = num
        if FLAG.exists():
            FLAG.unlink()
    else:
        old = state.get("fingerprints", {})
        opened = []
        for t, d in sorted(threads.items()):
            f = fp_of(t, d, head)
            prev = old.get(t)
            if prev is not None and prev != f:
                title = "TRIPPED: #%s" % t
                ex = gh("issue", "list", "--repo", REPO, "--state", "open",
                        "--limit", "100", "--json", "number,title")
                try:
                    items = json.loads(ex.stdout or "[]")
                except Exception:
                    items = []
                if any(i.get("title") == title for i in items):
                    print("skip: open issue already exists for", t, flush=True)
                else:
                    diffs = ["%s: %s -> %s" % (lab, (prev.get(lab) if prev.get(lab) is not None else "?"),
                                               (f.get(lab) if f.get(lab) is not None else "?"))
                             for lab in LABELS
                             if (prev.get(lab) if t != "227" else prev.get(lab)) != (f.get(lab))]
                    diffs = [x for x in diffs if not x.endswith("-> ?") or t == "227"]
                    body_lines = (["تغيّر مرصود في الخيط المراقب #%s (فحص %s):" % (t, now)]
                                  + diffs[:4]
                                  + ["الرابط: " + THREADS[t],
                                     "النص الحرفي للتعليقات لا يُنسخ وفق v6.5b-3 — الرابط فقط."])
                    n = open_issue(title, "\n".join(body_lines[:10]))
                    print("opened TRIPPED issue #%s for thread %s" % (n, t), flush=True)
                    opened.append(t)
            state.setdefault("fingerprints", {})[t] = f
        if opened:
            print("trip-notify opened:", ",".join(opened), flush=True)

    state["updated"] = now
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n")
    print("trip-notify done", flush=True)


if __name__ == "__main__":
    main()

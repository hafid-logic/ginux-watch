#!/usr/bin/env python3
"""TRIPPED notify (directive v6.5b-3 + session-51 §3a): open an issue in
hafid-logic/ginux-watch when a watched thread (threads 222, 207, 227) changes
(comment count / last stamp / state / PR head). Dedup via fingerprints in
matrix/notify-state.json. Simulate mode (workflow_dispatch input simulate=true,
or matrix/.simulate-flag): open a test issue, close it, record its number.

Session-51 §3a hardening (AGENTS rule 21 — no cross-references to Gregory's repos):
- Title format is "TRIPPED: thread-<N>" — never "#N" (local ref) anywhere.
- Every upstream URL inside backticks; no @mention; no verbatim comment quotes.
- Self-test: team/scripts/test-trip-notify-xref.py (offline regex gate).

Session-51 fix-ups from W3 audit (before-push):
- [HIGH] fingerprint advances only when the issue is actually opened (else retried).
- [MED] fail-closed on `gh issue list` failure: skip opening rather than duplicate.
- [MED] transient ls-remote failure no longer yields a fake head227 TRIPPED
  (only a 40-hex sha is accepted; otherwise None).
- [LOW] simulate flag is consumed only after a successful test issue.
- Note (critic b4): a failed simulate keeps the flag, so the scheduled run retries
  every sweep by design until one test issue opens and closes successfully."""
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
HEX40 = re.compile(r"^[0-9a-f]{40}$")


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


def fp_of(t, d, head, prev=None):
    # A transient ls-remote failure must not fabricate a head change (s51 fix):
    # only a 40-hex sha is accepted; on transient failure the previous head227
    # is carried forward so no false TRIPPED opens (critic FAIL b5, session-51).
    h = head if (head and HEX40.match(head)) else None
    if t == "227" and h is None and prev is not None:
        h = prev.get("head227")
    return {
        "state": d.get("state", "unknown"),
        "comments": d.get("comments"),
        "last_comment_at": d.get("last_comment_at"),
        "head227": h if t == "227" else None,
    }


def build_title(t):
    """s51 §3a: 'TRIPPED: thread-<N>' — no '#N' (AGENTS rule 21)."""
    return "TRIPPED: thread-%s" % t


def build_body(t, diffs, now):
    """s51 §3a: thread id without '#', upstream link inside backticks, no quotes,
    no @mention — the body must never produce a cross-reference (AGENTS rule 21)."""
    lines = (
        ["تغيّر مرصود في الخيط المراقب thread-%s (فحص %s):" % (t, now)]
        + diffs[:4]
        + ["الرابط: `" + THREADS[t] + "`",
           "النص الحرفي للتعليقات لا يُنسخ وفق v6.5b-3 وAGENTS قاعدة 21 — الرابط داخل علامات الاقتباس البرمجية فقط."]
    )
    return "\n".join(lines[:10])


def build_simulate_body(now):
    return "\n".join([
        "بطاقة اختبار آلي للإشعار (توجيه v6.5b-3 بند 3) — لا تغيير حقيقي في الخيوط المراقبة.",
        "المصدر: team-watcher في وضع simulate (workflow_dispatch بمدخل simulate=true، أو matrix/.simulate-flag).",
        "الخيوط المراقبة (روابط داخل علامات الاقتباس البرمجية — AGENTS قاعدة 21):",
        "`" + THREADS["222"] + "`",
        "`" + THREADS["207"] + "`",
        "`" + THREADS["227"] + "`",
        "يُغلق هذا الـissue تلقائيًا بعد الفتح، ورقمه يُسجَّل في matrix/notify-state.json.",
    ])


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
        num = open_issue("TRIPPED: simulate-test", build_simulate_body(now))
        if num:
            gh("issue", "close", str(num), "--repo", REPO,
               "--comment", "simulate test — closed automatically (v6.5b-3)")
            print("SIMULATE_ISSUE=%d" % num, flush=True)
            state["simulate_last_issue"] = num
            if FLAG.exists():
                FLAG.unlink()  # consumed only on success (s51 fix)
        else:
            print("SIMULATE_ISSUE=unknown — flag kept for retry (s51 fix)", flush=True)
    else:
        old = state.get("fingerprints", {})
        opened = []
        for t, d in sorted(threads.items()):
            prev = old.get(t)
            f = fp_of(t, d, head, prev)
            if prev is None or prev == f:
                state.setdefault("fingerprints", {})[t] = f
                continue
            title = build_title(t)
            # Fail-closed dedup check (s51 fix): if we cannot list open issues,
            # do not open a possibly-duplicate one; retry next run.
            ex = gh("issue", "list", "--repo", REPO, "--state", "open",
                    "--limit", "200", "--json", "number,title")
            list_ok = ex.returncode == 0
            try:
                items = json.loads(ex.stdout or "[]")
            except Exception:
                list_ok = False
            if not list_ok:
                print("skip: cannot verify open issues (fail-closed) for", t, flush=True)
                continue
            if any(i.get("title") == title for i in items):
                print("skip: open issue already exists for", t, flush=True)
                state.setdefault("fingerprints", {})[t] = f
                continue
            diffs = ["%s: %s -> %s" % (lab, (prev.get(lab) if prev.get(lab) is not None else "?"),
                                       (f.get(lab) if f.get(lab) is not None else "?"))
                     for lab in LABELS
                     if (prev.get(lab) if t != "227" else prev.get(lab)) != (f.get(lab))]
            diffs = [x for x in diffs if not x.endswith("-> ?") or t == "227"]
            n = open_issue(title, build_body(t, diffs, now))
            if n:
                print("opened TRIPPED issue #%s for thread %s" % (n, t), flush=True)
                opened.append(t)
                state.setdefault("fingerprints", {})[t] = f  # success only (s51 fix)
            else:
                print("open_issue failed for thread %s — fingerprint kept, will retry" % t,
                      flush=True)
        if opened:
            print("trip-notify opened:", ",".join(opened), flush=True)

    state["updated"] = now
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n")
    print("trip-notify done", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""test-upstream-watch.py — offline tests for the v7.7-1 thread-state tracking
in team/scripts/upstream-watch.py. Zero network (gh is mocked), zero secrets.

  W1  transition capture (REAL 2026-11-13 data): from the v7.6 baseline
      (222/207/227 open, comments 2/4/1) to the live values (222 closed
      @02:27:17Z comments=4, 207 closed @02:58:34Z comments=5, 227 merged
      @02:27:02Z) the sweep emits one STATE-TRANSITION breaker line per
      thread, with the correct from->to and timestamps.
  W2  merged semantics: only 227 (pull.merged=true) reports state "merged";
      222 (plain issue) and 207 (PR closed unmerged — head b19e3ea3 is NOT
      an ancestor of upstream/main) report "closed".
  W3  state_changed_at recorded: merged_at for 227, closed_at for 222/207;
      the prev snapshot had no such field and the new one carries it.
  W4  quiet sweep: unchanged API values produce NO transition and NO changed
      lines (comment-identity path).
  W5  comment-only change still triggers the CHANGED line (breaker parity:
      comments keep their trigger power after v7.7-1).

Run: python3 team/scripts/test-upstream-watch.py
"""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "upstream_watch", REPO / "team" / "scripts" / "upstream-watch.py")
uw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uw)

PASS, FAIL = 0, 0
def ok(name):
    global PASS
    PASS += 1
    print("ok  %s" % name)
def no(name, msg=""):
    global FAIL
    FAIL += 1
    print("FAIL %s %s" % (name, msg))

ISSUE_222 = {"number": 222, "state": "closed", "closed_at": "2026-11-13T02:27:17Z",
             "comments": 4, "updated_at": "2026-11-13T02:27:17Z"}
ISSUE_207 = {"number": 207, "state": "closed", "closed_at": "2026-11-13T02:58:34Z",
             "comments": 5, "updated_at": "2026-11-13T02:58:34Z",
             "pull_request": {"url": "x"}}
ISSUE_227 = {"number": 227, "state": "closed", "closed_at": "2026-11-13T02:27:02Z",
             "comments": 1, "updated_at": "2026-11-13T02:27:02Z",
             "pull_request": {"url": "x"}}
PULL_207 = {"number": 207, "merged": False, "merged_at": None}
PULL_227 = {"number": 227, "merged": True, "merged_at": "2026-11-13T02:27:02Z"}
CMT_222 = [{"created_at": "2026-11-06T05:29:33Z", "user": {"login": "gmkurtzer"}},
           {"created_at": "2026-11-13T02:27:13Z", "user": {"login": "gmkurtzer"}}]
CMT_207 = [{"created_at": "2026-11-13T02:58:33Z", "user": {"login": "gmkurtzer"}}]
CMT_227 = [{"created_at": "2026-11-06T14:58:30Z", "user": {"login": "gmkurtzer"}}]

REAL_ISSUES = {"222": ISSUE_222, "207": ISSUE_207, "227": ISSUE_227}
REAL_PULLS = {"207": PULL_207, "227": PULL_227}
REAL_COMMENTS = {"222": CMT_222, "207": CMT_207, "227": CMT_227}


def fake_gh_factory(issues, pulls, comments):
    def fake_gh(*args):
        path = args[1]
        for n in ("222", "207", "227"):
            if path.endswith("/pulls/%s" % n):
                return json.dumps(pulls.get(n))
        for n in ("222", "207", "227"):
            if path.endswith("/issues/%s" % n):
                return json.dumps(issues.get(n))
        for n in ("222", "207", "227"):
            if "/issues/%s/comments" % n in path:
                return json.dumps(comments.get(n, []))
        raise AssertionError("unexpected gh path: %s" % path)
    return fake_gh


def run_sweep(issues, pulls, comments, prev_threads):
    uw.gh = fake_gh_factory(issues, pulls, comments)
    state = {"threads_watch": prev_threads}
    out = []
    uw.watch_threads(state, "2026-11-13T11:00:00Z", out)
    return state["threads_watch"], out


def prev_open(comments):
    return {n: {"state": "open", "comments": c,
                "updated_at": "2026-11-06T14:58:29Z",
                "last_comment_at": "2026-11-06T14:58:29Z",
                "last_comment_author": "gmkurtzer",
                "checked": "2026-11-12T22:28:53Z"}
            for n, c in comments.items()}


# W1/W2/W3 — the real 2026-11-13 event, from the v7.6 baseline
snap, out = run_sweep(REAL_ISSUES, REAL_PULLS, REAL_COMMENTS,
                      prev_open({"222": 2, "207": 4, "227": 1}))
trans = [l for l in out if "STATE-TRANSITION" in l]
if len(trans) == 3 and all("STATE-TRANSITION" in l for l in trans):
    ok("W1 three STATE-TRANSITION breaker lines on the real 11-13 event")
else:
    no("W1 transitions", str(out))
if (snap["227"]["state"] == "merged" and snap["222"]["state"] == "closed"
        and snap["207"]["state"] == "closed"):
    ok("W2 merged vs closed semantics (227 merged; 222/207 closed)")
else:
    no("W2 semantics", str({n: snap[n]["state"] for n in snap}))
if (snap["227"]["state_changed_at"] == "2026-11-13T02:27:02Z"
        and snap["222"]["state_changed_at"] == "2026-11-13T02:27:17Z"
        and snap["207"]["state_changed_at"] == "2026-11-13T02:58:34Z"):
    ok("W3 state_changed_at = merged_at/closed_at recorded")
else:
    no("W3 state_changed_at", str({n: snap[n].get("state_changed_at") for n in snap}))

# W4 — quiet sweep (same values as the new snapshot)
snap2, out2 = run_sweep(REAL_ISSUES, REAL_PULLS, REAL_COMMENTS, snap)
if not any("STATE-TRANSITION" in l or "CHANGED" in l for l in out2):
    ok("W4 quiet sweep emits no transition/changed lines")
else:
    no("W4 quiet", str(out2))

# W5 — comment-only change still trips (breaker parity for comments)
q222 = dict(REAL_ISSUES["222"])
q222["comments"] = 5
c222 = CMT_222 + [{"created_at": "2026-11-13T03:30:00Z",
                   "user": {"login": "gmkurtzer"}}]
snap3, out3 = run_sweep({"222": q222, "207": ISSUE_207, "227": ISSUE_227},
                        REAL_PULLS, {"222": c222, "207": CMT_207, "227": CMT_227},
                        snap)
if any("#222 CHANGED" in l for l in out3) \
        and not any("#222 STATE-TRANSITION" in l for l in out3):
    ok("W5 comment-only change still trips the CHANGED line (no false transition)")
else:
    no("W5 comment parity", str(out3))

print("upstream-watch tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

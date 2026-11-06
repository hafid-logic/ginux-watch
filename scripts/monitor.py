#!/usr/bin/env python3
"""monitor.py — light read-only upstream monitor (v3.6 §2b/2c).

Snapshots gmkurtzer/ginux (main sha, README cutoff text, tags, archive
branches, open issue/PR counts, watched items #4/#14/#43/#54/#58/#61,
involves/mentions search counts) and gmkurtzer/ginux-us (existence, first
commits, README/CONTRIBUTING) using `gh api` GET calls only. Diffs the
snapshot against the state file and, on significant change, opens ONE digest
issue in this repository (body <= 10 lines). No change -> no digest.

Knobs (env):
  GH_BIN          gh executable path            (default: gh)
  MONITOR_STATE   state file path               (default: state/monitor.json)
  MONITOR_DRY_RUN "1" -> print snapshot+diff; never update an existing state
                  file, create issues, or commit/push. Seeds a baseline state
                  only when the state file does not exist yet (so a second
                  dry run has something to diff against). In CI
                  (GITHUB_REPOSITORY set, non-dry-run) a fresh baseline is also
                  committed so the next scheduled run can diff against it.

Robustness: every API section is failure-isolated; a failing section logs to
stderr and keeps the PREVIOUS value, so our own tooling breakage never
fabricates a digest. Exit 0 even with section failures; exit 2 only when gh
auth itself fails. All upstream access is READ-ONLY.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

GH_BIN = os.environ.get("GH_BIN", "gh")
STATE = os.environ.get("MONITOR_STATE", "state/monitor.json")
DRY_RUN = os.environ.get("MONITOR_DRY_RUN") == "1"

UPSTREAM = "gmkurtzer/ginux"
UPSTREAM_US = "gmkurtzer/ginux-us"
OUR_LOGIN = "hafid-logic"
WATCHED = ["4", "14", "43", "54", "58", "61", "222"]  # 222: our overflow-checks question (v5.1-13, 2026-11-06)
BULLET_CAP = 6
BODY_CAP = 10
GH_TIMEOUT = 60


class GHError(Exception):
    """A gh api call failed (non-404)."""


class NotFoundError(GHError):
    """A gh api call returned HTTP 404."""


# ---------------------------------------------------------------- gh helpers

def gh_run(*args):
    """Run gh with args; never raises (timeouts become rc=124)."""
    try:
        return subprocess.run(
            [GH_BIN, *args], capture_output=True, text=True, timeout=GH_TIMEOUT
        )
    except FileNotFoundError:
        sys.stderr.write(f"monitor: gh executable not found: {GH_BIN!r}\n")
        sys.exit(2)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args, 124, stdout="", stderr=f"timeout after {GH_TIMEOUT}s"
        )


def _err(p):
    return (p.stderr or "").strip()


def gh_json(*args):
    """gh api -> parsed JSON; NotFoundError on HTTP 404, GHError otherwise."""
    p = gh_run("api", *args)
    if p.returncode != 0:
        if "HTTP 404" in _err(p):
            raise NotFoundError(_err(p)[:200])
        raise GHError(f"gh api {args[0] if args else ''}: {_err(p)[:200]}")
    return json.loads(p.stdout)


def gh_text(*args):
    """gh api -> raw stdout text (for raw media types)."""
    p = gh_run("api", *args)
    if p.returncode != 0:
        if "HTTP 404" in _err(p):
            raise NotFoundError(_err(p)[:200])
        raise GHError(f"gh api {args[0] if args else ''}: {_err(p)[:200]}")
    return p.stdout


def gh_exists(*args):
    """True if the API path exists, False on 404, GHError on other failures."""
    p = gh_run("api", *args)
    if p.returncode == 0:
        return True
    if "HTTP 404" in _err(p):
        return False
    raise GHError(f"gh api {args[0] if args else ''}: {_err(p)[:200]}")


# ------------------------------------------------------------------ snapshot

def blank_snapshot():
    """Snapshot skeleton with EXACTLY the tracked keys."""
    return {
        "checked_utc": None,
        "ginux": {
            "main_sha": None,
            "readme_sha": None,
            "release_count": None,
            "tags": [],
            "archive_branches": [],
            "open_issues": None,
            "open_prs": None,
            "latest_number": None,
            "last_push_utc": None,
        },
        "ginux_us": {
            "exists": False,
            "pushed_at": None,
            "default_branch": None,
            "has_issues": False,
            "readme_sha": None,
            "contributing": False,
            "first_commits": [None, None, None],
        },
        "watched": {
            n: {"state": None, "updated_at": None, "comments": None, "reactions": None, "labels": None}
            for n in WATCHED
        },
        "mentions": {"involves": None, "mentions": None, "repo_name": None},
    }


def seed_from_previous(snap, prev):
    """Pre-fill the snapshot with previous state values (failure isolation:
    a section that fails below simply keeps these)."""
    if not isinstance(prev, dict):
        return
    for g in ("ginux", "ginux_us", "mentions"):
        pg = prev.get(g)
        if isinstance(pg, dict):
            for k, v in pg.items():
                if k in snap[g]:
                    snap[g][k] = v
    pw = prev.get("watched")
    if isinstance(pw, dict):
        for n in WATCHED:
            if isinstance(pw.get(n), dict):
                for k, v in pw[n].items():
                    if k in snap["watched"][n]:
                        snap["watched"][n][k] = v


def first_line(msg):
    if not msg:
        return ""
    return msg.splitlines()[0][:80]


# ---- API sections (each wrapped in try/except by the runner) ----

def sec_main_sha(snap):
    snap["ginux"]["main_sha"] = gh_json(f"repos/{UPSTREAM}/commits/main")["sha"]


def sec_readme(snap):
    # v4.0 §0b (2026-11-05): cutoff/pivot literals are historical — README tracked by sha only.
    meta = gh_json(f"repos/{UPSTREAM}/readme")
    snap["ginux"]["readme_sha"] = meta.get("sha")


def sec_releases(snap):
    rel = gh_json(f"repos/{UPSTREAM}/releases?per_page=100")
    snap["ginux"]["release_count"] = len(rel)


def sec_tags(snap):
    tags = gh_json(f"repos/{UPSTREAM}/tags?per_page=5")[:5]
    snap["ginux"]["tags"] = [
        {"name": t.get("name"), "sha": (t.get("commit") or {}).get("sha")} for t in tags
    ]


def sec_branches(snap):
    brs = gh_json(f"repos/{UPSTREAM}/branches?per_page=100")
    # v3.6 §2b(أ): archive markers = names containing "archive" OR the measured
    # standalone-kernel archive branch/tag family "bootable" (branch bootable-kernel,
    # tag bootable-kernel-final @4d4a53bb — T-20261105-06, 2026-11-05T05:48Z).
    MARKERS = ("archive", "bootable")
    snap["ginux"]["archive_branches"] = sorted(
        b.get("name", "")
        for b in brs
        if any(m in str(b.get("name", "")).lower() for m in MARKERS)
    )


def sec_counts(snap):
    prs = gh_json(f"repos/{UPSTREAM}/pulls?state=open&per_page=100")
    issues_all = gh_json(f"repos/{UPSTREAM}/issues?state=open&per_page=100")
    issues = [i for i in issues_all if i.get("pull_request") is None]
    nums = [x.get("number", 0) for x in prs] + [x.get("number", 0) for x in issues]
    snap["ginux"]["open_prs"] = len(prs)
    snap["ginux"]["open_issues"] = len(issues)
    snap["ginux"]["latest_number"] = max(nums) if nums else 0


def sec_pushed_at(snap):
    snap["ginux"]["last_push_utc"] = gh_json(f"repos/{UPSTREAM}").get("pushed_at")


def sec_watched(snap):
    for n in WATCHED:
        it = gh_json(f"repos/{UPSTREAM}/issues/{n}")
        snap["watched"][n] = {
            "state": it.get("state"),
            "updated_at": it.get("updated_at"),
            "comments": it.get("comments"),
            "reactions": (it.get("reactions") or {}).get("total_count"),
            "labels": len(it.get("labels") or []),
        }


def sec_mentions(snap):
    inv = gh_json(
        f"search/issues?q=repo:{UPSTREAM}+involves:{OUR_LOGIN}&per_page=1"
    ).get("total_count")
    men = gh_json(
        f"search/issues?q=repo:{UPSTREAM}+mentions:{OUR_LOGIN}&per_page=1"
    ).get("total_count")
    # v4.0 §0b: also catch references to our WATCH repo name upstream.
    rep = gh_json(
        f"search/issues?q=repo:{UPSTREAM}+ginux-watch&per_page=1"
    ).get("total_count")
    snap["mentions"] = {"involves": inv, "mentions": men, "repo_name": rep}


def sec_us(snap):
    absent = {
        "exists": False,
        "pushed_at": None,
        "default_branch": None,
        "has_issues": False,
        "readme_sha": None,
        "contributing": False,
        "first_commits": [None, None, None],
    }
    try:
        repo = gh_json(f"repos/{UPSTREAM_US}")
    except NotFoundError:
        snap["ginux_us"] = absent
        return
    d = dict(snap["ginux_us"])  # keep previous values for sub-call failures
    d["exists"] = True
    d["pushed_at"] = repo.get("pushed_at")
    d["default_branch"] = repo.get("default_branch")
    d["has_issues"] = bool(repo.get("has_issues"))
    try:
        d["readme_sha"] = gh_json(f"repos/{UPSTREAM_US}/readme").get("sha")
    except GHError as e:
        sys.stderr.write(f"monitor: ginux-us readme: {e}\n")
    try:
        d["contributing"] = gh_exists(f"repos/{UPSTREAM_US}/contents/CONTRIBUTING.md")
    except GHError as e:
        sys.stderr.write(f"monitor: ginux-us CONTRIBUTING: {e}\n")
    try:
        commits = gh_json(f"repos/{UPSTREAM_US}/commits?per_page=3") or []
        d["first_commits"] = [
            {
                "sha": c.get("sha"),
                "date": (c.get("commit") or {}).get("author", {}).get("date"),
                "message": first_line((c.get("commit") or {}).get("message")),
            }
            for c in commits[:3]
        ]
        while len(d["first_commits"]) < 3:
            d["first_commits"].append(None)
    except GHError as e:
        sys.stderr.write(f"monitor: ginux-us commits: {e}\n")
    snap["ginux_us"] = d


SECTIONS = [
    ("ginux.main_sha", sec_main_sha),
    ("ginux.readme", sec_readme),
    ("ginux.tags", sec_tags),
    ("ginux.releases", sec_releases),
    ("ginux.branches", sec_branches),
    ("ginux.counts", sec_counts),
    ("ginux.pushed_at", sec_pushed_at),
    ("watched", sec_watched),
    ("mentions", sec_mentions),
    ("ginux_us", sec_us),
]


# ----------------------------------------------------------------- diffing

def normalize(obj, path=""):
    """Prepare values for comparison: tags as ordered 'name@sha' strings,
    first_commits as 'sha@date@message' strings; everything else as-is."""
    if isinstance(obj, dict):
        return {k: normalize(obj[k], f"{path}.{k}" if path else k) for k in obj}
    if isinstance(obj, list):
        if path == "ginux.tags":
            return [
                "%s@%s" % (e.get("name"), e.get("sha")) if isinstance(e, dict) else str(e)
                for e in obj
            ]
        if path == "ginux_us.first_commits":
            return [
                "%s@%s@%s" % (e.get("sha"), e.get("date"), e.get("message"))
                if isinstance(e, dict)
                else ("" if e is None else str(e))
                for e in obj
            ]
        return list(obj)
    return obj


def deep_diff(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            deep_diff(a.get(k), b.get(k), f"{path}.{k}" if path else k, out)
        return
    if a != b:
        out.append((path, a, b))


def fmt_val(v, limit=100):
    if isinstance(v, list):
        s = "[" + "; ".join(str(x) for x in v) + "]"
    elif v is None:
        s = "null"
    elif isinstance(v, bool):
        s = "true" if v else "false"
    else:
        s = str(v)
    return s if len(s) <= limit else s[: limit - 1] + "…"


# ------------------------------------------------------------------ digest

def pick_link(changes):
    paths = [p for p, _, _ in changes]
    if any(p == "ginux.readme_sha" for p in paths):
        return f"https://raw.githubusercontent.com/{UPSTREAM}/main/README.md"
    ids = sorted(
        {p.split(".")[1] for p in paths if p.startswith("watched.")}, key=int
    )
    if ids:
        return f"https://github.com/{UPSTREAM}/issues/{ids[0]}"
    if any(p.startswith("ginux_us") for p in paths):
        return f"https://github.com/{UPSTREAM_US}"
    return f"https://github.com/{UPSTREAM}"


def decide(changes):
    """(نعم/لا, short reason) — decision-critical changes first."""
    paths = [p for p, _, _ in changes]
    # v4.0 §0b: freeze-text indicators removed — significant = main progress,
    # our watched items, mentions of us/our repo, ginux-us, releases/tags, README direction.
    if "ginux.main_sha" in paths:
        return "نعم", "التزام جديد على main في المنبع"
    if any(p.startswith("watched.") for p in paths):
        return "نعم", "تحديث على أحد عناصرنا المراقَبة"
    if any(p.startswith("mentions.") for p in paths):
        return "نعم", "إشارة/رد جديد يخص حسابنا أو مستودعنا"
    if any(p.startswith("ginux_us.") for p in paths):
        return "نعم", "تطوّر في ginux-us"
    if "ginux.release_count" in paths:
        return "نعم", "Release جديد في المنبع"
    if "ginux.readme_sha" in paths:
        return "نعم", "تغيّر README المنبع (اتجاه/توثيق)"
    if "ginux.latest_number" in paths:
        return "نعم", "عنصر جديد (issue/PR) في المنبع"
    return "لا", "تغييرات منخفضة الأهمية فقط (وسوم/فروع/عدّادات)"


def build_digest(checked_utc, changes):
    """<= 10 lines: header + <=6 bullets (+overflow note) + link + decision."""
    bullets = [f"- {p}: {fmt_val(o)} → {fmt_val(n)}" for p, o, n in changes[:BULLET_CAP]]
    lines = [f"تغيّر مهم في المراقبة — {checked_utc}", *bullets]
    if len(changes) > BULLET_CAP:
        lines.append(f"… و{len(changes) - BULLET_CAP} تغييرات أخرى (التفصيل في state/monitor.json)")
    lines.append(f"الرابط: {pick_link(changes)}")
    verdict, reason = decide(changes)
    lines.append(f"يحتاج قرارًا؟ {verdict} — {reason}")
    if len(lines) > BODY_CAP:  # hard cap; unreachable by construction
        lines = lines[:BODY_CAP]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ actions

def create_issue(checked_utc, body):
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        sys.stderr.write("monitor: GITHUB_REPOSITORY unset → skip issue create\n")
        return
    with open("/tmp/digest.md", "w", encoding="utf-8") as f:
        f.write(body)
    p = gh_run(
        "issue", "create", "-R", repo,
        "--title", f"monitor digest {checked_utc}",
        "--body-file", "/tmp/digest.md",
    )
    if p.returncode != 0:
        sys.stderr.write(f"monitor: issue create failed: {_err(p)[:300]}\n")
    else:
        print(f"issue created: {(p.stdout or '').strip()}")


def write_state(snap):
    d = os.path.dirname(STATE)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp, STATE)


def git(args):
    return subprocess.run(["git", *args], capture_output=True, text=True, timeout=120)


def commit_push(checked_utc):
    git(["config", "user.name", "monitor"])
    git(["config", "user.email", "actions@users.noreply.github.com"])
    pr = git(["pull", "--rebase", "--autostash", "origin", "main"])
    if pr.returncode != 0:
        sys.stderr.write(f"monitor: git pull failed: {_err(pr)[:300]}\n")
    git(["add", STATE])
    cm = git(["commit", "-m", f"monitor state {checked_utc} [skip ci]"])
    if cm.returncode != 0:
        sys.stderr.write(f"monitor: git commit failed: {_err(cm)[:300]}\n")
        return
    push = git(["push"])
    if push.returncode != 0:
        sys.stderr.write("monitor: push failed → re-pull and retry once\n")
        git(["pull", "--rebase", "--autostash", "origin", "main"])
        push = git(["push"])
        if push.returncode != 0:
            sys.stderr.write(f"monitor: push retry failed: {_err(push)[:300]}\n")


# --------------------------------------------------------------------- main

def main():
    auth = gh_run("auth", "status")
    if auth.returncode != 0:
        sys.stderr.write(f"monitor: gh auth failed:\n{_err(auth)[:500]}\n")
        return 2

    prev = None
    if os.path.isfile(STATE):
        try:
            with open(STATE, encoding="utf-8") as f:
                prev = json.load(f)
        except (OSError, ValueError) as e:
            sys.stderr.write(f"monitor: state unreadable ({e}) → treating as missing\n")
            prev = None

    snap = blank_snapshot()
    seed_from_previous(snap, prev)

    failed = []
    for name, fn in SECTIONS:
        try:
            fn(snap)
        except Exception as e:  # failure isolation by design
            failed.append(name)
            sys.stderr.write(f"monitor: section {name} failed (kept previous value): {e}\n")

    snap["checked_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if DRY_RUN:
        print("snapshot:")
        print(json.dumps(snap, ensure_ascii=False, indent=2))

    if prev is None or not isinstance(prev, dict):
        if failed:
            sys.stderr.write(
                "monitor: baseline deferred — sections failed: " + ", ".join(failed) + "\n"
            )
            print("baseline deferred")
            return 0
        write_state(snap)
        print("baseline")
        if DRY_RUN:
            sys.stderr.write(f"monitor: dry-run seeded baseline → {STATE}\n")
        elif os.environ.get("GITHUB_REPOSITORY"):
            commit_push(snap["checked_utc"])
        return 0

    old = normalize({k: v for k, v in prev.items() if k != "checked_utc"})
    new = normalize({k: v for k, v in snap.items() if k != "checked_utc"})
    changes = []
    deep_diff(old, new, "", changes)
    changes.sort(key=lambda c: c[0])

    if not changes:
        print("no changes")
        return 0

    if DRY_RUN:
        print("diff:")
        for p, o, n in changes:
            print(f"- {p}: {fmt_val(o)} → {fmt_val(n)}")
        print("would create issue:")
        print(build_digest(snap["checked_utc"], changes))
        return 0

    body = build_digest(snap["checked_utc"], changes)
    create_issue(snap["checked_utc"], body)
    write_state(snap)
    if os.environ.get("GITHUB_REPOSITORY"):
        commit_push(snap["checked_utc"])
    else:
        sys.stderr.write("monitor: GITHUB_REPOSITORY unset → skip commit/push\n")
    print(f"digest written ({len(changes)} changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

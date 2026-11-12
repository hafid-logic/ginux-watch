#!/usr/bin/env python3
"""report_lint.py — deterministic lint for outbox reports (directive v7.5 clause 1).

First priority: runs on every NEW report in outbox/ — locally as part of the
pre-commit hook (scripts/hooks/install-pre-commit.sh) and as a CI step — and
appends its verdict to the report head as one line:

    lint: PASS (a,b,c,d,e,f,g,h) | at: <UTC> | tool: scripts/report_lint.py
    lint: FAIL (a,c) | at: <UTC> | tool: scripts/report_lint.py

Clauses (directive letters أ..ح mapped to a..h):
  a (أ) CLEAR claims must rest on API / git ls-remote evidence, never HTML.
  b (ب) any TRIPPED claim requires a fresh diff against the saved baseline.
  c (ج) any evaluated patch: its target files must exist at main head
        (git cat-file -e HEAD:<path>).
  d (د) heartbeat: last_success is independent of last_run — a health claim
        must cite last_success (or the state file that carries it), never a
        bare last_run.
  e (هـ) CJK character check (same ranges as scripts/check_cjk.py).
  f (و) byte-level secret scan (same patterns as scripts/tree-token-scan.py);
        stricter than the tree gate: reports must not carry token-shaped
        strings at all, not even the sanctioned ghp_SYNTHETIC-EX-* form.
  g (ز) base_head in the report = origin/main at writing time (or explicitly
        marked older); lint verifies presence + git merge-base ancestry
        against origin/main (a stale-but-real head stays an ancestor).
  h (ح) mentioned paths must resolve inside the repo (tracked in git) or be
        tagged [sandbox] near the mention.

Exit codes: 0 = all PASS, 1 = any FAIL, 2 = usage error.
NEVER prints matched secret text — only path + clause + pattern class.
"""
import argparse
import datetime
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CLAUSE_IDS = ["a", "b", "c", "d", "e", "f", "g", "h"]
LINT_LINE_RE = re.compile(r"^lint: (PASS|FAIL) \(([^)]*)\) \| at: (\S+) \| tool: scripts/report_lint\.py", re.M)

# ---- reusable gates imported from the existing scripts (single source) ----
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_cjk = _load("report_lint_check_cjk", REPO / "scripts" / "check_cjk.py")
_tok = _load("report_lint_tree_token_scan", REPO / "scripts" / "tree-token-scan.py")
CJK_RANGES = _cjk.CJK_RANGES
TOKEN_PATTERNS = _tok.PATTERNS
ALLOWED_SYNTHETIC = _tok.ALLOWED_SYNTHETIC

# ---- clause a: CLEAR / صافٍ claims ----
CLEAR_WORDS = ("CLEAR", "صافٍ", "صافي")
API_EVIDENCE = ("api.github.com", "ls-remote", "github api", "rest api",
                "via api", "عبر api", "عبر واجهة api", "measured api")
HTML_EVIDENCE = ("html", "webfetch", "الخام")

# ---- clause b: TRIPPED claims ----
SHA_ARROW_RE = re.compile(r"\b[0-9a-f]{7,40}\s*(?:→|->|=>)\s*[0-9a-f]{7,40}\b", re.I)
TRIP_DIFF_WORDS = ("baseline", "خط الأساس", "الأساس")
TRIP_DIFF_PROOF = ("فرق", "diff", "تغيّر", "تغير", "changed", "new_activity")

# ---- clause d: heartbeat ----
HB_WORDS = ("heartbeat", "النبض", "نبض team-watcher")
HB_HEALTH_WORDS = ("سليمة", "سليم", "healthy", "مستمر", "لا إنذار", "good")
HB_STATE_FILES = ("matrix/upstream-watch.json", "state/heartbeat")

# ---- clause h: paths ----
CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
PATH_SHAPE_RE = re.compile(r"^[~A-Za-z0-9._/<>{}\-]+(/[~A-Za-z0-9._/<>{}\-]+)+/?$")
PLACEHOLDER_RE = re.compile(r"<[^<>]+>|\{[^{}]+\}")
SANDBOX_TAGS = ("[sandbox]", "[خارج المستودع]", "[outside]", "[sandbox-only]")
SANDBOX_PREFIXES = ("/tmp/", "/data/", "~/.ssh", "work/keys/", "work/.config/")
FORWARD_ONLY = ("http://", "https://", "ssh://", "git@", "ftp://")


def utcnow():
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _window(lines, idx, before=3, after=3):
    lo = max(0, idx - before)
    hi = min(len(lines), idx + after + 1)
    return "\n".join(lines[lo:hi]).lower()


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True)


def lint_text(text, relpath="<memory>"):
    """Run clauses a..h over report text. Returns (verdict, failed_ids, details)."""
    lines = text.splitlines()
    low_lines = [ln.lower() for ln in lines]
    details = []          # list of (clause, severity, message) — severity: fail|warn
    failed = []

    def fail(clause, msg):
        details.append((clause, "fail", msg))
        if clause not in failed:
            failed.append(clause)

    # ---- (a) CLEAR / صافٍ claims need API or ls-remote evidence ----
    for i, ln in enumerate(lines):
        if any(w in ln for w in CLEAR_WORDS):
            win = _window(lines, i)
            if not any(m in win for m in API_EVIDENCE):
                if any(m in win for m in HTML_EVIDENCE):
                    fail("a", "line %d: CLEAR claim with HTML-only evidence" % (i + 1))
                else:
                    fail("a", "line %d: CLEAR claim without API/ls-remote evidence in window" % (i + 1))

    # ---- (b) TRIPPED claims need a fresh diff vs saved baseline ----
    for i, ln in enumerate(lines):
        if "TRIPPED" in ln or "tripped" in low_lines[i]:
            win = _window(lines, i)
            ok = bool(SHA_ARROW_RE.search(win))
            if not ok and any(w in win for w in TRIP_DIFF_WORDS):
                ok = any(w in win for w in TRIP_DIFF_PROOF)
            if not ok:
                fail("b", "line %d: TRIPPED claim without fresh baseline diff evidence" % (i + 1))

    # ---- (c) evaluated patch targets must exist at main head ----
    in_diff = False
    targets = []
    for ln in lines:
        if ln.startswith("```"):
            lang = ln[3:].strip().lower()
            if not in_diff and lang in ("diff", "patch"):
                in_diff = True
            elif in_diff:
                in_diff = False
            continue
        if in_diff and ln.startswith("+++ "):
            tgt = ln[4:].strip()
            if tgt.startswith("b/"):
                tgt = tgt[2:]
            if tgt and tgt != "/dev/null":
                targets.append(tgt)
    for tgt in targets:
        r = git("cat-file", "-e", "HEAD:%s" % tgt)
        if r.returncode != 0:
            fail("c", "patch target missing at HEAD: %s" % tgt)

    # ---- (d) heartbeat: last_success independent of last_run ----
    for i, ln in enumerate(lines):
        if any(w in ln for w in HB_WORDS):
            # health claim must live at the mention itself (±1 line) — a bare
            # 'heartbeat' inside a test name must not inherit a health word
            # from an unrelated paragraph
            win = _window(lines, i, before=1, after=1)
            has_health = any(w in win for w in HB_HEALTH_WORDS)
            if not has_health:
                continue
            ok = ("last_success" in win) or any(f in win for f in HB_STATE_FILES) \
                or ("alert_basis" in win)
            if not ok:
                fail("d", "line %d: heartbeat health claim without last_success/state-file basis" % (i + 1))

    # ---- (e) CJK ----
    for ch in text:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in CJK_RANGES):
            fail("e", "CJK character U+%04X in report" % cp)
            break

    # ---- (f) secrets, byte-level ----
    data = text.encode("utf-8", "surrogateescape")
    for cls, pat in TOKEN_PATTERNS:
        if pat.search(data):
            fail("f", "full-form token pattern (%s) in report — redact immediately" % cls)
    # stricter than the tree gate: reports never carry token-shaped strings,
    # not even the sanctioned ghp_SYNTHETIC-EX-* fixture form (redact to
    # sha256-12 fingerprint instead).
    if ALLOWED_SYNTHETIC.search(data):
        fail("f", "token-shaped string (ghp_SYNTHETIC-EX-*, synthetic form) — redact to sha256-12 in reports")

    # ---- (g) base_head field + ancestry vs origin/main ----
    fm = front_matter(text)
    base = None
    if fm:
        m = re.search(r"^base_head:\s*([0-9a-f]{7,40})\s*$", fm, re.M)
        if m:
            base = m.group(1)
    if base is None:
        fail("g", "base_head field missing from report head")
    else:
        r = git("merge-base", "--is-ancestor", base, "origin/main")
        if r.returncode != 0:
            fail("g", "base_head %s is not an ancestor of origin/main (stale/fabricated base)" % base)

    # ---- (h) mentioned paths resolve in repo or tagged [sandbox] ----
    checked = set()
    BARE_PATH_RE = re.compile(
        r"\b(?:upload|work|state|scripts|eval|docs|reports|directives|inbox|"
        r"matrix|team|outbox|config)/[A-Za-z0-9._/<>{\-]+")
    def _spans(line, in_fence):
        found = list(CODE_SPAN_RE.findall(line))
        if in_fence:
            # fenced diff/patch content is code, not a prose path mention
            return found
        for m in BARE_PATH_RE.findall(line):
            if m not in found:
                found.append(m)
        return found
    in_fence = False
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            in_fence = not in_fence
        for span in _spans(ln, in_fence):
            span = span.strip().rstrip(".,؛:-")
            if span in checked or len(span) > 120 or " " in span or "*" in span:
                continue
            if any(span.startswith(p) for p in FORWARD_ONLY):
                continue
            if not PATH_SHAPE_RE.match(span):
                continue
            # GitHub owner/repo slugs and similar two-segment labels are not
            # filesystem paths (hafid-logic/ginux-watch)
            parts = span.split("/")
            if len(parts) == 2 and "." not in parts[1] and parts[0] not in (
                    "upload", "work", "state", "scripts", "eval", "docs",
                    "reports", "directives", "inbox", "matrix", "team",
                    "outbox", "config"):
                continue
            checked.add(span)
            win = _window(lines, i, before=1, after=1)
            tagged = any(t in win for t in SANDBOX_TAGS)
            resolved = _resolves_in_repo(span)
            if resolved:
                continue
            if tagged:
                continue
            fail("h", "path `%s` (line %d) not tracked in repo and not tagged [sandbox]" % (span, i + 1))

    verdict = "PASS" if not failed else "FAIL"
    return verdict, failed, details


def _resolves_in_repo(p):
    """True when p names repo content: tracked in git, or present in the
    working tree and NOT gitignored (sandbox-only locations like work/.config,
    work/keys are gitignored = not repo content; upload/ is outside the repo
    entirely)."""
    candidates = [p, PLACEHOLDER_RE.sub("x", p)]
    for c in candidates:
        c = c.strip("/")
        if c.startswith(SANDBOX_PREFIXES) or c.startswith("./") or c.startswith("~"):
            return False
        if c.startswith("/"):
            return False
        r = git("ls-files", "--", c)
        if r.stdout.strip():
            return True
        parent = "/".join(c.split("/")[:-1])
        if PLACEHOLDER_RE.search(p) and parent:
            r = git("ls-files", "--", parent)
            if r.stdout.strip():
                return True
        # present in the working tree and not gitignored -> repo content
        if parent:
            pr = git("check-ignore", "-q", c)
            if pr.returncode == 1 and (REPO / c).exists():
                return True
    return False


def front_matter(text):
    """Return the YAML front-matter block (without --- fences) or ''. """
    lines = text.splitlines()
    for start in range(min(3, len(lines))):  # may follow a status line (v7.5-5)
        if lines[start].strip() == "---":
            for end in range(start + 1, min(start + 60, len(lines))):
                if lines[end].strip() == "---":
                    return "\n".join(lines[start + 1:end])
            break
    return ""


def lint_line(verdict, failed):
    clauses = ",".join(failed) if failed else ",".join(CLAUSE_IDS)
    return "lint: %s (%s) | at: %s | tool: scripts/report_lint.py" % (verdict, clauses, utcnow())


def apply_lint_line(text, verdict, failed):
    """Insert/replace the lint: line inside the front-matter (or at top)."""
    newline = lint_line(verdict, failed)
    text = re.sub(r"^lint: (PASS|FAIL) \([^)]*\) \| at: \S+ \| tool: scripts/report_lint\.py\n",
                  "", text, flags=re.M)
    lines = text.splitlines(keepends=True)
    # front-matter may be preceded by a supervisor status line (v7.5-5) —
    # locate the opening '---' within the first 3 lines
    for start in range(min(3, len(lines))):
        if lines[start].rstrip("\n") == "---":
            for end in range(start + 1, min(start + 40, len(lines))):
                if lines[end].rstrip("\n") == "---":
                    return "".join(lines[:end]) + newline + "\n" + "".join(lines[end:])
            break
    return newline + "\n" + text


def stale_check(text, verdict, failed):
    """--check mode: an existing lint: line must match the fresh verdict."""
    m = LINT_LINE_RE.search(text)
    if not m:
        return "missing lint line"
    old_v, old_c = m.group(1), m.group(2)
    new_c = ",".join(failed) if failed else ",".join(CLAUSE_IDS)
    if old_v != verdict or old_c != new_c:
        return "stale lint line (recorded %s %s vs computed %s %s)" % (old_v, old_c, verdict, new_c)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="deterministic lint for outbox reports (v7.5-1)")
    ap.add_argument("paths", nargs="+", help="report .md files (or dirs) to lint")
    ap.add_argument("--check", action="store_true",
                    help="verify only: fail when the lint: line is missing or stale")
    ap.add_argument("--fix", action="store_true",
                    help="append/update the lint: line in the report head")
    ap.add_argument("--json", action="store_true", help="machine summary to stdout")
    args = ap.parse_args(argv)
    if args.check and args.fix:
        print("usage error: --check and --fix are mutually exclusive", file=sys.stderr)
        return 2

    files = []
    for p in args.paths:
        pp = Path(p)
        if pp.is_dir():
            files += sorted(x for x in pp.glob("*.md")
                            if x.name not in ("INDEX.md", "LATEST.md", "_TEMPLATE.md"))
        else:
            files.append(pp)

    results, any_fail = [], False
    for f in files:
        text = f.read_text(encoding="utf-8", errors="surrogateescape")
        verdict, failed, details = lint_text(text, str(f))
        row = {"file": str(f), "verdict": verdict, "failed": failed, "details": [d for _, _, d in details]}
        if args.check:
            problem = stale_check(text, verdict, failed)
            if problem:
                row["check"] = problem
                verdict = "FAIL"
                row["verdict"] = "FAIL"
        if args.fix:
            new_text = apply_lint_line(text, verdict, failed)
            if new_text != text:
                f.write_text(new_text, encoding="utf-8")
                row["lint_line_updated"] = True
        if verdict == "FAIL":
            any_fail = True
        results.append(row)

    if args.json:
        print(json.dumps({"results": results, "ok": not any_fail},
                         ensure_ascii=False, indent=1))
    else:
        for row in results:
            head = "%s: %s" % (row["file"], row["verdict"])
            if row["failed"]:
                head += " (%s)" % ",".join(row["failed"])
            print(head)
            for d in row["details"]:
                print("   -", d)
            if "check" in row:
                print("   - check:", row["check"])
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())

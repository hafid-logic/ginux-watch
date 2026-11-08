#!/usr/bin/env python3
"""Sanitize our own watch issues so they stop cross-referencing upstream repos
(session-51 §3b, AGENTS rule 21).

Runs in GitHub Actions with the internal GITHUB_TOKEN only (issues: write,
scoped to this single job — .github/workflows/issue-sanitize.yml). Never touches
Gregory's repos (read-only universe), never posts comments.

Behavior for each target issue (default: 7 and 9):
  1. Fetch title+body (gh api).
  2. Retitle: replace every '#N' with 'thread-N' (e.g. "TRIPPED: #207" ->
     "TRIPPED: thread-207"). Titles without '#N' are kept.
  3. Body: wrap every bare URL / #N / owner/repo#N / @mention that sits OUTSIDE
     existing backtick spans (and outside fenced code blocks) in backticks.
  4. PATCH the issue (unless DRY_RUN=true).
  5. If CLOSE_9=true and DRY_RUN=false: close issue 9 (breaker batch absorbed).

Self-test: python3 team/scripts/issue-sanitize.py --selftest (offline)."""
import json
import os
import re
import subprocess
import sys

REPO = os.environ.get("GITHUB_REPOSITORY", "hafid-logic/ginux-watch")
TARGETS = (7, 9)
REPO_PARTS = tuple(x for x in REPO.split("/") if x)


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("gh failed: %s" % ((r.stderr or r.stdout) or "")[:300])
    return r.stdout


def gh_soft(*args):
    """gh call returning (ok, stdout_or_err) — 404 tolerated (issue absent)."""
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    blob = (r.stderr or r.stdout or "")
    if r.returncode == 0:
        return True, r.stdout
    if "404" in blob or "Not Found" in blob or "not found" in blob:
        return False, "404"
    return False, blob[:300]


# --- code-span aware sanitizing -------------------------------------------

SPAN = re.compile(r"`[^`\n]*`")
FENCE = re.compile(r"^\s*(```|~~~)", re.M)
BARE_URL = re.compile(r"(?<!`)\bhttps?://[^\s<>()`]+")
HASH_REF = re.compile(r"(?<![\w/&`])#([0-9]+)\b")
REPO_HASH = re.compile(r"(?<!`)\b([A-Za-z0-9][\w.\-]*)/([A-Za-z0-9][\w.\-]*)#([0-9]+)\b")
MENTION = re.compile(r"(?<![\w.@/`])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)")


def _wrap_outside(text, pattern, repl):
    """Apply `pattern`→`repl` only outside existing backtick spans and fenced blocks."""
    spans = list(SPAN.finditer(text))
    # blank out fenced blocks line-ranges first (they lose their content protection
    # only if unbackticked; fenced blocks are protected via placeholder)
    fences = list(FENCE.finditer(text))
    prot = []
    out = text
    # protect fenced regions by pairing fence markers
    if len(fences) >= 2:
        marks = [f.start() for f in fences]
        for i in range(0, len(marks) - 1, 2):
            prot.append((marks[i], marks[i + 1]))
    def protected(pos):
        for a, b in prot:
            if a <= pos < b:
                return True
        for s in spans:
            if s.start() <= pos < s.end():
                return True
        return False

    result = []
    last = 0
    for m in pattern.finditer(out):
        if protected(m.start()):
            continue
        result.append(out[last:m.start()])
        result.append(repl(m))
        last = m.end()
    result.append(out[last:])
    return "".join(result)


def outside_protected(text):
    """Return only the characters sanitizing treats as unprotected
    (same span/fence logic as _wrap_outside) — used by the selftest so the
    scan matches the implementation exactly."""
    spans = list(SPAN.finditer(text))
    fences = list(FENCE.finditer(text))
    prot = []
    if len(fences) >= 2:
        marks = [f.start() for f in fences]
        for i in range(0, len(marks) - 1, 2):
            prot.append((marks[i], marks[i + 1]))

    def covered(pos):
        for a, b in prot:
            if a <= pos < b:
                return True
        for s in spans:
            if s.start() <= pos < s.end():
                return True
        return False

    return "".join(ch for pos, ch in enumerate(text) if not covered(pos))


def sanitize_body(body):
    if not body:
        return body
    t = _wrap_outside(body, REPO_HASH,
                      lambda m: "`%s/%s#%s`" % (m.group(1), m.group(2), m.group(3)))
    t = _wrap_outside(t, BARE_URL, lambda m: "`%s`" % m.group(0))
    t = _wrap_outside(t, HASH_REF, lambda m: "`#%s`" % m.group(1))
    t = _wrap_outside(t, MENTION, lambda m: "`@%s`" % m.group(1))
    return t


def sanitize_title(title):
    """'#N' -> 'thread-N' (AGENTS rule 21). Titles without '#N' are unchanged."""
    if "#" not in title:
        return title
    return re.sub(r"#([0-9]+)\b", r"thread-\1", title)


def selftest():
    # Note (critic j2): the scan below reuses outside_protected() — it validates
    # the wrapping result, but cannot catch a systematic flaw shared by both the
    # implementation and the scan. The regex gate in test-trip-notify-xref.py is
    # the independent check for emitted titles/bodies.
    bad_body = ("Thread #207 changed.\n"
                "Link: https://github.com/gmkurtzer/ginux/pull/207 and gmkurtzer/ginux#207\n"
                "ping @gmkurtzer but keep `https://inside.example/x` as-is\n"
                "```\nfenced https://github.com/gmkurtzer/ginux stays\n```\n"
                "mail me not: someone@example.com\n")
    good = sanitize_body(bad_body)
    for pat, why in ((re.compile(r"(?<!`)https?://"), "bare URL"),
                     (re.compile(r"(?<![\w/&`])#207\b"), "hash ref"),
                     (re.compile(r"(?<!`)gmkurtzer/ginux#207"), "repo#N"),
                     (re.compile(r"(?<![\w.@/`])@gmkurtzer\b"), "mention")):
        # outside backticks there must be no unsanitized form; scan uses the
        # exact same protection logic as the implementation
        stripped = outside_protected(good)
        if pat.search(stripped):
            raise AssertionError("selftest failed: %s still outside backticks" % why)
    assert "`https://inside.example/x`" in good
    t1 = sanitize_title("TRIPPED: #207")
    assert t1 == "TRIPPED: thread-207", t1
    t2 = sanitize_title("TRIPPED: simulate-test")
    assert t2 == "TRIPPED: simulate-test", t2
    # email addresses must not be turned into mentions
    t3 = sanitize_body("contact someone@example.com about #7")
    assert "someone@example.com" in t3 and "`@example" not in t3
    print("issue-sanitize selftest: OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    dry = os.environ.get("DRY_RUN", "false").strip().lower() == "true"
    close_9 = os.environ.get("CLOSE_9", "true").strip().lower() == "true"
    owner, name = REPO_PARTS
    absent = []
    for n in TARGETS:
        ok, blob = gh_soft("api", "repos/%s/%s/issues/%d" % (owner, name, n))
        if not ok:
            # session-52: issues 7 and 9 were deleted via the GitHub UI
            # (breaker batch absorbed). Absence is a normal end-state: report
            # and continue — no crash, no PATCH.
            print("issue %d: ABSENT (already deleted/sanitized) — skip" % n, flush=True)
            absent.append(n)
            continue
        issue = json.loads(blob)
        title = sanitize_title(issue.get("title") or "")
        body = sanitize_body(issue.get("body") or "")
        print("issue %d: title %r -> %r, body %d -> %d chars"
              % (n, (issue.get("title") or "")[:40], title[:40],
                 len(issue.get("body") or ""), len(body)), flush=True)
        if not dry:
            gh("api", "-X", "PATCH", "repos/%s/%s/issues/%d" % (owner, name, n),
               "-f", "title=%s" % title, "-f", "body=%s" % body)
            print("issue %d patched" % n, flush=True)
        else:
            print("issue %d: dry-run, not patched" % n, flush=True)
        if n == 9 and close_9 and not dry:
            gh("api", "-X", "PATCH", "repos/%s/%s/issues/9" % (owner, name),
               "-f", "state=closed")
            print("issue 9 closed (breaker batch absorbed, s51 §2)", flush=True)
    print("sanitize summary: %d target(s), %d absent" % (len(TARGETS), len(absent)), flush=True)


if __name__ == "__main__":
    main()

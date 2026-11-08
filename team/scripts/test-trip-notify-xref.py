#!/usr/bin/env python3
"""Cross-reference gate v2 (session-52, directive v6.3 item 4; extends s51 §3a).

Two layers, CI-fail on any unwrapped reference:

L1 DYNAMIC — every emitted title/body of every text generator is generated
   here with sample inputs and asserted clean:
     - team/scripts/trip-notify.py (build_title/build_body/build_simulate_body)
     - scripts/monitor.py (digest issue title + build_digest body)
   Clean means: no '#N', no 'owner/repo#N', no '@mention', no bare URL
   outside backticks, and (titles) no literal '#'.

L2 STATIC — every text-generator SOURCE file is scanned for unwrapped
   reference forms, so a future generator cannot grow a bad template:
     - .github/workflows/*.yml  (line scan, shell-comment aware, ${{ }} masked)
     - scripts/*.py, team/scripts/*.py (AST scan of ALL string literals,
       docstrings included)
     - scripts/*.sh, team/scripts/*.sh (line scan, comments INCLUDED —
       comments are prose and must follow the 'PR N' style too)
   Forbidden in L2: '#N' and 'owner/repo#N' (bare-URL/mention checks stay in
   L1 because workflow sources legitimately contain curl URLs and uses:@v4).

ALLOWLIST (files whose FUNCTION requires known-bad samples; their samples are
offline test data, never emitted to GitHub surfaces):
     - this file (positive controls for the patterns)
     - team/scripts/issue-sanitize.py (selftest samples)

Style rule (directive v6.3): automated texts say 'PR 207' / 'thread 222',
never '#207'. No network, no gh, no git. Run: python3
team/scripts/test-trip-notify-xref.py   (exit 0 = clean)."""
import ast
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (this file: team/scripts/)
ALLOWLIST = {
    "team/scripts/test-trip-notify-xref.py",  # positive controls (this file)
    "team/scripts/issue-sanitize.py",         # selftest samples
}

# --- forbidden cross-reference forms (outside backtick spans) ---
RE_BARE_URL = re.compile(r"https?://[^\s`]")
RE_HASH_REF = re.compile(r"(?:^|\s)#[0-9]+\b")
RE_REPO_HASH = re.compile(r"\b[\w.\-]+/[\w.\-]+#[0-9]+\b")
RE_MENTION = re.compile(r"(?<![\w.@])@[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")

# --- L2 forms (reference hygiene in generator sources) ---
L2_HASH = re.compile(r"(?:^|(?<![\w&/]))#[0-9]+\b")
L2_REPO_HASH = re.compile(r"\b[A-Za-z0-9][\w.\-]*/[A-Za-z0-9][\w.\-]*#[0-9]+\b")


def strip_backticks(text):
    return re.sub(r"`[^`]*`", "", text)


def assert_clean(text, label):
    stripped = strip_backticks(text)
    for pat, name in (
        (RE_BARE_URL, "bare URL"),
        (RE_HASH_REF, "#N reference"),
        (RE_REPO_HASH, "owner/repo#N"),
        (RE_MENTION, "@mention"),
    ):
        m = pat.search(stripped)
        if m:
            raise AssertionError(
                "%s: emitted a %s (near <%s>)" % (label, name, m.group(0)[:40])
            )
    if isinstance(text, str) and "#" in text and "backtick" not in label:
        raise AssertionError("%s: title/body still contains a literal '#'" % label)


def selftest_patterns():
    """Positive controls: each pattern must catch a known-bad sample."""
    samples = {
        RE_BARE_URL: "see https://github.com/gmkurtzer/ginux/pull/207 here",
        RE_HASH_REF: "thread changed #207 ok",
        RE_REPO_HASH: "fix gmkurtzer/ginux#207 now",
        RE_MENTION: "ping @gmkurtzer about it",
    }
    for pat, sample in samples.items():
        if not pat.search(strip_backticks(sample)):
            raise AssertionError("selftest: pattern failed on positive sample %r" % sample)
    clean = "الرابط: `https://github.com/gmkurtzer/ginux/issues/222` وthread-222"
    for pat in (RE_BARE_URL, RE_HASH_REF, RE_REPO_HASH, RE_MENTION):
        if pat.search(strip_backticks(clean)):
            raise AssertionError("selftest: backticked URL wrongly flagged")
    print("selftest patterns: OK")


def _load(relpath, modname):
    spec = importlib.util.spec_from_file_location(modname, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def l1_dynamic():
    tn = _load("team/scripts/trip-notify.py", "trip_notify")
    now = "2026-11-08T00:00:00Z"
    for t in sorted(tn.THREADS):
        title = tn.build_title(t)
        body = tn.build_body(
            t,
            ["comments: 3 -> 4", "last_comment_at: 2026-11-06T14:58:28Z -> 2026-11-07T16:29:20Z"],
            now,
        )
        assert_clean(title, "title thread-%s" % t)
        assert_clean(body, "body thread-%s" % t)
        if "thread-" not in title:
            raise AssertionError("title lacks thread- form: %r" % title)
    assert_clean("TRIPPED: simulate-test", "title simulate")
    assert_clean(tn.build_simulate_body(now), "body simulate")
    fp = tn.fp_of("227", {"state": "open", "comments": 1}, "unknown")
    if fp["head227"] is not None:
        raise AssertionError("fp_of accepted 'unknown' head")
    fp_carry = tn.fp_of("227", {"state": "open", "comments": 1}, "unknown",
                        {"head227": "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf"})
    if fp_carry["head227"] != "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf":
        raise AssertionError("fp_of did not carry forward prev head227")
    fp_new = tn.fp_of("227", {"state": "open", "comments": 1},
                      "53a54addea67969abaa240ea478def1b94130eee",
                      {"head227": "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf"})
    if fp_new["head227"] != "53a54addea67969abaa240ea478def1b94130eee":
        raise AssertionError("fp_of did not accept a genuine new head")
    fp_ok = tn.fp_of("227", {"state": "open", "comments": 1},
                     "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf")
    if fp_ok["head227"] != "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf":
        raise AssertionError("fp_of rejected valid 40-hex head")
    print("L1 trip-notify: 3 titles + 3 bodies + simulate clean, fp_of guarded")

    mon = _load("scripts/monitor.py", "monitor_mod")
    body = mon.build_digest(
        now,
        [("upstream main", "53a54addea6", "9b11baea12c"),
         ("thread 207 comments", "4", "5"),
         ("thread 227 head", "9ac0f544f7f1", "5ae058f21190")],
    )
    assert_clean(body, "monitor digest body")
    assert_clean("monitor digest %s" % now, "monitor digest title")
    print("L1 monitor: digest title + body clean")


# --- L2 static scan ---------------------------------------------------------

def l2_scan_python(rel):
    """AST scan: every string constant (docstrings included) must be ref-free."""
    src = (ROOT / rel).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(rel))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if len(val) < 4:
                continue
            for pat, name in ((L2_HASH, "#N"), (L2_REPO_HASH, "owner/repo#N")):
                m = pat.search(val)
                if m:
                    raise AssertionError(
                        "%s:%d string literal has unwrapped %s (<%s>)"
                        % (rel, getattr(node, "lineno", 0), name, m.group(0)[:30])
                    )


def l2_mask_yaml_sh(text):
    """Mask GitHub expressions and inline shell params that confuse the scan."""
    text = re.sub(r"\$\{\{[^}]*\}\}", "GHEXPR", text)
    text = re.sub(r"\$\(\([^)]*\)\)", "ARITH", text)
    return text


def l2_scan_lines(rel, include_comments):
    text = (ROOT / rel).read_text(encoding="utf-8")
    text = l2_mask_yaml_sh(text)
    for i, line in enumerate(text.splitlines(), 1):
        probe = line
        if not include_comments:
            probe = re.sub(r"(?<![:\w])#.*$", "", probe)
        for pat, name in ((L2_HASH, "#N"), (L2_REPO_HASH, "owner/repo#N")):
            m = pat.search(probe)
            if m:
                raise AssertionError(
                    "%s:%d unwrapped %s (<%s>): %s"
                    % (rel, i, name, m.group(0)[:30], line.strip()[:80])
                )


def l2_static():
    scanned = {"py": [], "yml": [], "sh": []}
    for rel in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        l2_scan_lines(".github/workflows/" + rel.name, include_comments=True)
        scanned["yml"].append(rel.name)
    for d in ("scripts", "team/scripts"):
        for rel in sorted((ROOT / d).glob("*.py")):
            rp = d + "/" + rel.name
            if rp in ALLOWLIST:
                continue
            l2_scan_python(rp)
            scanned["py"].append(rp)
        for rel in sorted((ROOT / d).glob("*.sh")):
            rp = d + "/" + rel.name
            if rp in ALLOWLIST:
                continue
            l2_scan_lines(rp, include_comments=True)
            scanned["sh"].append(rp)
    print("L2 static: %d yml + %d py + %d sh generator sources ref-free"
          % (len(scanned["yml"]), len(scanned["py"]), len(scanned["sh"])))


def main():
    selftest_patterns()
    l1_dynamic()
    l2_static()
    print("xref gate v2: OK — dynamic emitters clean + static generators clean")


if __name__ == "__main__":
    main()

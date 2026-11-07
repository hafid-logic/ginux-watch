#!/usr/bin/env python3
"""Offline cross-reference gate for trip-notify.py (session-51 §3a, AGENTS rule 21).

Proves that every title/body trip-notify can emit contains:
  - no '#N' issue reference (title or body)
  - no 'owner/repo#N' reference
  - no '@mention'
  - no bare URL outside backticks
The regex patterns are first validated against known-bad positive samples
(selftest), so the gate cannot pass vacuously. No network, no gh, no git.

Run: python3 team/scripts/test-trip-notify-xref.py   (exit 0 = clean)"""
import importlib.util
import re
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "trip_notify", Path(__file__).resolve().parent / "trip-notify.py"
)
trip_notify = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(trip_notify)

# --- patterns for forbidden cross-reference forms (outside backtick spans) ---
RE_BARE_URL = re.compile(r"https?://[^\s`]")
RE_HASH_REF = re.compile(r"(?:^|\s)#[0-9]+\b")
RE_REPO_HASH = re.compile(r"\b[\w.\-]+/[\w.\-]+#[0-9]+\b")
RE_MENTION = re.compile(r"(?<![\w.@])@[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")


def strip_backticks(text):
    """Remove code spans so content inside backticks is not scanned."""
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
                "%s: %s emitted a %s (near <%s>)" % (label, type(text).__name__, name, m.group(0)[:40])
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
    # inside backticks must NOT be flagged
    clean = "الرابط: `https://github.com/gmkurtzer/ginux/issues/222` وthread-222"
    for pat in (RE_BARE_URL, RE_HASH_REF, RE_REPO_HASH, RE_MENTION):
        if pat.search(strip_backticks(clean)):
            raise AssertionError("selftest: backticked URL wrongly flagged")
    print("selftest patterns: OK")


def main():
    selftest_patterns()
    now = "2026-11-08T00:00:00Z"
    # 1) real TRIPPED titles+bodies for every watched thread
    for t in sorted(trip_notify.THREADS):
        title = trip_notify.build_title(t)
        body = trip_notify.build_body(
            t,
            ["comments: 3 -> 4", "last_comment_at: 2026-11-06T14:58:28Z -> 2026-11-07T16:29:20Z"],
            now,
        )
        assert_clean(title, "title thread-%s" % t)
        assert_clean(body, "body thread-%s" % t)
        if "thread-" not in title:
            raise AssertionError("title lacks thread- form: %r" % title)
    # 2) simulate title+body
    assert_clean("TRIPPED: simulate-test", "title simulate")
    assert_clean(trip_notify.build_simulate_body(now), "body simulate")
    # 3) fingerprints must not fabricate heads on transient ls-remote failure
    fp = trip_notify.fp_of("227", {"state": "open", "comments": 1}, "unknown")
    if fp["head227"] is not None:
        raise AssertionError("fp_of accepted 'unknown' head")
    # 3b) carry-forward: with a previous head, a transient failure keeps it (no false TRIPPED)
    fp_carry = trip_notify.fp_of("227", {"state": "open", "comments": 1}, "unknown",
                                 {"head227": "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf"})
    if fp_carry["head227"] != "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf":
        raise AssertionError("fp_of did not carry forward prev head227")
    # 3c) a genuine new head still wins over the carried-forward value
    fp_new = trip_notify.fp_of("227", {"state": "open", "comments": 1},
                               "53a54addea67969abaa240ea478def1b94130eee",
                               {"head227": "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf"})
    if fp_new["head227"] != "53a54addea67969abaa240ea478def1b94130eee":
        raise AssertionError("fp_of did not accept a genuine new head")
    fp_ok = trip_notify.fp_of("227", {"state": "open", "comments": 1},
                              "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf")
    if fp_ok["head227"] != "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf":
        raise AssertionError("fp_of rejected valid 40-hex head")
    print("xref gate: OK — 3 titles + 3 bodies + simulate clean, fp_of guarded (carry-forward)")


if __name__ == "__main__":
    main()

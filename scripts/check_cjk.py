#!/usr/bin/env python3
"""check_cjk.py — gate: reject CJK characters in Markdown deliverables (v7.1 item 7).

Scans every .md under outbox/, reports/, docs/, directives/ (repo-relative) and
fails (exit 1) if any CJK character is found: Chinese (U+3400-4DBF, U+4E00-9FFF,
U+F900-FAFF, U+20000-2A6DF), Japanese kana (U+3040-309F, U+30A0-30FF, U+31F0-31FF),
Hangul (U+1100-11FF, U+3130-318F, U+AC00-D7AF), CJK punctuation (U+3000-303F).

Exemption: a file containing the exact marker line `CJK-EXEMPT-VERBATIM-ARCHIVE`
is skipped — that marker is reserved for verbatim directive archives whose bytes
must match the received text (sha256 recorded in directives/INDEX.md).

Usage: python3 scripts/check_cjk.py [paths...]   (default: the four gated dirs)
Must run before every commit; installed locally as .git/hooks/pre-commit.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DIRS = ["outbox", "reports", "docs", "directives"]
EXEMPT_MARKER = "CJK-EXEMPT-VERBATIM-ARCHIVE"

CJK_RANGES = (
    (0x3000, 0x303F),   # CJK Symbols and Punctuation
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
    (0x31F0, 0x31FF),   # Katakana Phonetic Extensions
    (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x3130, 0x318F),   # Hangul Compatibility Jamo
    (0xAC00, 0xD7AF),   # Hangul Syllables
    (0x20000, 0x2A6DF), # CJK Unified Ideographs Extension B
)


def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in CJK_RANGES)


def main(argv):
    if len(argv) > 1:
        roots = [Path(p) for p in argv[1:]]
    else:
        roots = [REPO / d for d in DEFAULT_DIRS]
    findings = []
    scanned = exempted = 0
    for root in roots:
        if root.is_file() and root.suffix == ".md":
            files = [root]
        elif root.is_dir():
            files = sorted(root.rglob("*.md"))
        else:
            continue
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as e:
                findings.append(f"{f}: unreadable ({e})")
                continue
            if EXEMPT_MARKER in text:
                exempted += 1
                continue
            scanned += 1
            for ln, line in enumerate(text.splitlines(), 1):
                for col, ch in enumerate(line, 1):
                    if is_cjk(ch):
                        findings.append(
                            f"{f}:{ln}:{col}: U+{ord(ch):04X} '{ch}'"
                        )
    if exempted:
        print(f"check_cjk: {exempted} file(s) skipped via {EXEMPT_MARKER} (verbatim archives)")
    print(f"check_cjk: scanned {scanned} Markdown file(s)")
    if findings:
        print(f"check_cjk: FAIL — {len(findings)} CJK occurrence(s):")
        for item in findings[:50]:
            print(f"  {item}")
        return 1
    print("check_cjk: PASS — no CJK characters in gated Markdown")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""tree-token-scan.py — v6.6 item 5 (directive v6.6, 2026-11-08).
CI gate: fail when ANY full-form token pattern exists in the WORKING TREE,
except the sanctioned synthetic fixture form ghp_SYNTHETIC-EX-*.
Prints only path + pattern class + match count. NEVER prints the matched text.
Exit codes: 0 = clean, 1 = hit found, 2 = usage error.
"""
import re
import sys
from pathlib import Path

PATTERNS = [
    ("ghp_", re.compile(rb"ghp_[A-Za-z0-9]{36}")),
    ("github_pat_", re.compile(rb"github_pat_[A-Za-z0-9_]{22,}")),
    ("nvapi-", re.compile(rb"nvapi-[A-Za-z0-9_\-]{20,}")),
    ("sk-", re.compile(rb"sk-[A-Za-z0-9_\-]{20,}")),
    ("AIza", re.compile(rb"AIza[0-9A-Za-z_\-]{35}")),
]
ALLOWED_SYNTHETIC = re.compile(rb"ghp_SYNTHETIC-EX-[A-Za-z0-9_\-]*")

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}


def scan() -> int:
    hits = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for cls, pat in PATTERNS:
            count = 0
            for m in pat.finditer(data):
                if ALLOWED_SYNTHETIC.search(m.group(0)):
                    continue
                count += 1
            if count:
                rel = p.relative_to(ROOT)
                print(f"HIT pattern-class={cls} count={count} path={rel}")
                hits += count
    if hits:
        print(f"FAIL: {hits} full-form token-pattern hit(s) in tree")
        return 1
    print("OK: no full-form token pattern in tree (ghp_SYNTHETIC-* fixtures allowed)")
    return 0


if __name__ == "__main__":
    sys.exit(scan())

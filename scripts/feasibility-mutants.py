#!/usr/bin/env python3
"""feasibility-mutants.py — cargo-mutants mutants.tsv → markdown survivors report (§4b).

Input: mutants.out/mutants.tsv written by `cargo mutants` (tab-separated, with a
header row). Columns are located DYNAMICALLY by header name (status / mutation /
file / line / function — plus common aliases), so any column order works; unknown
status vocabularies are counted as-is. Output counts total/caught/timeout/
not-treated (+ any other statuses) and lists SURVIVED mutants sorted by file,line.

If the TSV is missing/empty/unparseable → a "no output (timeout before any
result)" document is written and the script exits 0 (partial results, if any,
stay in the uploaded mutants.tsv artifact).

Usage:
  python3 scripts/feasibility-mutants.py \
      --tsv upstream/mutants.out/mutants.tsv --out mutants-survived.md \
      --crate ginux-volume-format

Selftest: python3 scripts/feasibility-mutants.py --selftest
Python3 stdlib only.
"""

import argparse
import csv
import sys
import tempfile
from pathlib import Path

SURVIVED_CAP = 100
_KNOWN_STATUS_ORDER = ("caught", "survived", "timeout", "nottreated")


def md_cell(s):
    return s.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _header_row_index(lines):
    for i, raw in enumerate(lines[:5]):
        cells = next(csv.reader([raw], delimiter="\t"), [])
        low = [c.strip().lower() for c in cells]
        if "status" in low and ("mutation" in low or "mutated_code" in low or "diff" in low):
            return i
    return None


def load_rows(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    hdr = _header_row_index(lines)
    if hdr is None:
        return []
    reader = csv.reader(lines[hdr:], delimiter="\t")
    header = next(reader)
    col = {c.strip().lower(): j for j, c in enumerate(header)}

    def pick(row, *names):
        for n in names:
            j = col.get(n)
            if j is not None and j < len(row):
                return row[j].strip()
        return ""

    rows = []
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        rows.append({
            "status": pick(row, "status"),
            "mutation": pick(row, "mutation", "mutated_code", "diff"),
            "file": pick(row, "file", "file_path", "path"),
            "line": pick(row, "line", "line_number"),
            "function": pick(row, "function", "fn", "function_name"),
        })
    return rows


def _line_key(r):
    return int(r["line"]) if r["line"].isdigit() else 10 ** 9


def build_md(rows, crate):
    counts = {}
    for r in rows:
        st = r["status"] or "(blank)"
        counts[st] = counts.get(st, 0) + 1
    ordered = [k for k in counts if k.lower() in _KNOWN_STATUS_ORDER]
    ordered.sort(key=lambda k: _KNOWN_STATUS_ORDER.index(k.lower()))
    ordered += sorted(k for k in counts if k.lower() not in _KNOWN_STATUS_ORDER)
    survived = sorted(
        (r for r in rows if r["status"].lower() == "survived"),
        key=lambda r: (r["file"], _line_key(r), r["function"], r["mutation"]),
    )
    out = [
        "## cargo-mutants — {} (§4b)".format(crate),
        "",
        "المصدر: mutants.out/mutants.tsv (الأعمدة تُقرأ ديناميكيًا من سطر العناوين).",
        "",
        "| status | count |",
        "|---|---|",
    ]
    for st in ordered:
        out.append("| {} | {} |".format(md_cell(st), counts[st]))
    out.append("| **total** | {} |".format(len(rows)))
    out.append("")
    out.append("### SURVIVED (مرتبة حسب file, line) — {}".format(len(survived)))
    out.append("")
    if survived:
        out.append("| crate | file | line | function | mutation |")
        out.append("|---|---|---|---|---|")
        for r in survived[:SURVIVED_CAP]:
            out.append("| {} | {} | {} | {} | {} |".format(
                md_cell(crate), md_cell(r["file"]), md_cell(r["line"]),
                md_cell(r["function"]), md_cell(r["mutation"])))
        out.append("")
        if len(survived) > SURVIVED_CAP:
            out.append("…and {} more (cap {})".format(len(survived) - SURVIVED_CAP, SURVIVED_CAP))
            out.append("")
        out.append("القائمة الكاملة (مع وصف كل طفرة) في mutants.tsv داخل الأرتيفكت.")
    else:
        out.append("لا توجد طفرات ناجية (no survived mutants).")
    return "\n".join(out) + "\n"


def no_output_md(crate):
    return (
        "## cargo-mutants — {} (§4b)\n"
        "\n"
        "no output (timeout before any result)\n"
        "\n"
        "لم يُنتج cargo-mutants ملف mutants.tsv — إمّا انتهت المهلة (timeout 1020s) قبل أي نتيجة\n"
        "أو فشل التشغيل. راجع step log وسجل التنفيذ (log tail) في الأرتيفكت.\n"
    ).format(crate)


SAMPLE_TSV = (
    "started\tstatus\tmutation\tfile\tline\tfunction\n"
    "2026-11-05T00:00:00Z\tCaught\tnegate return\tcrates/x/src/a.rs\t10\tdo_thing\n"
    "2026-11-05T00:00:01Z\tSurvived\tswap binary op\tcrates/x/src/a.rs\t12\tdo_thing\n"
    "2026-11-05T00:00:02Z\tSurvived\treplace + with -\tcrates/x/src/b.rs\t3\tadd_one\n"
    "2026-11-05T00:00:03Z\tTimeout\ttighten loop bound\tcrates/x/src/c.rs\t7\tspin\n"
    "2026-11-05T00:00:04Z\tNotTreated\t-\tcrates/x/src/c.rs\t9\tskip_me\n"
)


def selftest():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "mutants.tsv"
        p.write_text(SAMPLE_TSV, encoding="utf-8")
        rows = load_rows(p)
        assert len(rows) == 5, rows
        md = build_md(rows, "ginux-x")
    assert "| Caught | 1 |" in md, md
    assert "| Survived | 2 |" in md, md
    assert "| Timeout | 1 |" in md, md
    assert "| NotTreated | 1 |" in md, md
    assert "| **total** | 5 |" in md, md
    # survivors sorted by (file, line): a.rs:12 must come before b.rs:3
    i_a = md.index("crates/x/src/a.rs | 12")
    i_b = md.index("crates/x/src/b.rs | 3")
    assert i_a < i_b, (i_a, i_b)
    assert "no output (timeout before any result)" in no_output_md("ginux-x")
    print("selftest: OK (feasibility-mutants)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="cargo-mutants mutants.tsv → markdown survivors report (v3.3 §4b)")
    ap.add_argument("--tsv", help="path to mutants.out/mutants.tsv")
    ap.add_argument("--out", default="mutants-survived.md")
    ap.add_argument("--crate", default="crate")
    ap.add_argument("--selftest", action="store_true", help="run the embedded hermetic selftest and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.tsv:
        ap.error("--tsv is required (or use --selftest)")
    tsv = Path(args.tsv)
    if not tsv.is_file():
        md, reason = no_output_md(args.crate), "tsv missing"
    else:
        rows = load_rows(tsv)
        if not rows:
            md, reason = no_output_md(args.crate), "tsv empty/unparseable"
        else:
            md, reason = build_md(rows, args.crate), "{} mutants".format(len(rows))
    Path(args.out).write_text(md, encoding="utf-8")
    print("wrote {} ({})".format(args.out, reason))
    return 0


if __name__ == "__main__":
    sys.exit(main())

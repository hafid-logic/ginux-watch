#!/usr/bin/env python3
"""feasibility-coverage.py — lcov.info → markdown coverage summary + details (§4a).

يقرأ ملف lcov.info الناتج من `cargo llvm-cov --lcov` ويكتب ملفين:
  1) --out     coverage-summary.md : جدول تغطية لكل crate (lines / functions / branches %)
     + صف TOTAL — تُجمع القيم لكل ملف (LF/LH, FNF/FNH, BRF/BRH) ثم لكل crate.
  2) --details coverage-details.md : الدوال العامة غير المغطاة (uncovered `pub fn`،
     من FNDA count=0 مع مطابقة نصية في crates/<crate>/src) لكل crate — حزم المفسّرات
     (priority) أولًا ثم البقية — ثم الفروع غير المغطاة (uncovered BRDA) لحزم
     المفسّرات فقط (priority crates).

lcov records handled: SF:, FN: (skipped), FNDA:<count>,<name>,
BRDA:<line>,<block>,<branch>,<taken>, LF:/LH:, FNF:/FNH:, BRF:/BRH:, DA:<line>,<count>.
Missing sections are computed from DA/FNDA/BRDA when absent; duplicate SF: records
are merged (max per metric); missing BRDA/FN sections are handled gracefully.

crate = أول مكوّن بعد "crates/" في مسار SF (crates/oci/src/lib.rs → "oci").
--priority يقبل أسماء الحزم (ginux-oci) أو أسماء المجلدات (oci) — كلاهما يُطابق.

Usage (من جذر استنساخ upstream):
  python3 ../scripts/feasibility-coverage.py lcov.info --src crates \
      --out coverage-summary.md --details coverage-details.md \
      --priority ginux-oci,ginux-protocol-state,ginux-volume-format

Selftest (hermetic, no inputs): python3 feasibility-coverage.py --selftest
Python3 stdlib only — no external deps.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

FNDA_CAP = 40  # max uncovered public functions listed per crate (then "…and N more")
BRDA_CAP = 60  # max uncovered branch lines listed per priority crate
PRIORITY_DEFAULT = "ginux-oci,ginux-protocol-state,ginux-volume-format"


def _int_or_none(s):
    s = s.strip()
    return int(s) if s.isdigit() else None


class FileCov:
    """One SF: record (duplicate SF records are merged, max per metric)."""

    __slots__ = ("sf", "lf", "lh", "fnf", "fnh", "brf", "brh", "fnda", "brda", "da")

    def __init__(self, sf):
        self.sf = sf
        self.lf = self.lh = self.fnf = self.fnh = self.brf = self.brh = None
        self.fnda = {}  # function name -> max FNDA count
        self.brda = []  # (line, block, branch, taken) as strings
        self.da = {}    # line int -> max DA count

    def _maxset(self, attr, value):
        """Duplicate SF records share one FileCov: later values max-merge, never clobber."""
        mine = getattr(self, attr)
        setattr(self, attr, value if mine is None else max(mine, value))

    def finalize(self):
        # Fallbacks when a record section is missing from the tracefile.
        if self.lf is None:
            self.lf = len(self.da)
        if self.lh is None:
            self.lh = sum(1 for c in self.da.values() if c > 0)
        if self.fnf is None:
            self.fnf = len(self.fnda)
        if self.fnh is None:
            self.fnh = sum(1 for c in self.fnda.values() if c > 0)
        if self.brf is None:
            self.brf = len(self.brda)
        if self.brh is None:
            self.brh = sum(1 for t in self.brda if t not in ("0", "-"))


def parse_lcov(text):
    files = []
    by_sf = {}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("SF:"):
            sf = line[3:].strip()
            cur = by_sf.get(sf)
            if cur is None:
                cur = FileCov(sf)
                by_sf[sf] = cur
                files.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("FNDA:"):
            count, _, name = line[5:].partition(",")
            name = name.strip()
            cnt = _int_or_none(count)
            cnt = 0 if cnt is None else cnt
            if name:
                cur.fnda[name] = max(cur.fnda.get(name, 0), cnt)
        elif line.startswith("FN:"):
            pass  # declaration line; FNDA carries the counts we use
        elif line.startswith("BRDA:"):
            parts = line[5:].split(",")
            if len(parts) == 4:
                cur.brda.append(tuple(p.strip() for p in parts))
        elif line.startswith("LF:"):
            v = _int_or_none(line[3:])
            if v is not None:
                cur._maxset("lf", v)
        elif line.startswith("LH:"):
            v = _int_or_none(line[3:])
            if v is not None:
                cur._maxset("lh", v)
        elif line.startswith("FNF:"):
            v = _int_or_none(line[4:])
            if v is not None:
                cur._maxset("fnf", v)
        elif line.startswith("FNH:"):
            v = _int_or_none(line[4:])
            if v is not None:
                cur._maxset("fnh", v)
        elif line.startswith("BRF:"):
            v = _int_or_none(line[4:])
            if v is not None:
                cur._maxset("brf", v)
        elif line.startswith("BRH:"):
            v = _int_or_none(line[4:])
            if v is not None:
                cur._maxset("brh", v)
        elif line.startswith("DA:"):
            parts = line[3:].split(",")
            if len(parts) >= 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                ln = int(parts[0])
                cur.da[ln] = max(cur.da.get(ln, 0), int(parts[1]))
        elif line.startswith("end_of_record"):
            cur = None
    for fc in files:
        fc.finalize()
    return files


def crate_dir(sf):
    parts = sf.replace("\\", "/").split("/")
    for i in range(len(parts) - 1):
        if parts[i] == "crates" and parts[i + 1]:
            return parts[i + 1]
    return None


def strip_pkg_prefix(name):
    n = name.strip().lower()
    return n[len("ginux-"):] if n.startswith("ginux-") else n


def normalize_priority(priority_arg):
    dirs = []
    for p in (priority_arg or "").split(","):
        p = p.strip().lower()
        if p and p not in dirs:
            dirs.append(strip_pkg_prefix(p))
    return dirs


def is_priority_dir(dirname, prio_dirs):
    d = dirname.strip().lower()
    return d in prio_dirs or strip_pkg_prefix(d) in prio_dirs


def aggregate(files):
    grouped, other = {}, []
    for fc in files:
        d = crate_dir(fc.sf)
        if d is None:
            other.append(fc)
        else:
            grouped.setdefault(d, []).append(fc)
    return grouped, other


def sums(crate_files):
    s = {"lf": 0, "lh": 0, "fnf": 0, "fnh": 0, "brf": 0, "brh": 0, "files": 0}
    for fc in crate_files:
        for k in ("lf", "lh", "fnf", "fnh", "brf", "brh"):
            s[k] += getattr(fc, k) or 0
        s["files"] += 1
    return s


def pct(hit, found):
    if not found:
        return "n/a"
    return "{:.1f}".format(100.0 * hit / found)


def build_summary(grouped, n_other):
    out = [
        "## تغطية الاختبارات (cargo-llvm-cov → lcov) — §4a",
        "",
        "صف لكل crate (المجلد تحت `crates/`)؛ النسب من LF/LH و FNF/FNH و BRF/BRH المجموعة لكل ملف.",
        "",
        "| crate | lines % | functions % | branches % | lines hit/found | functions hit/found | branches hit/found |",
        "|---|---|---|---|---|---|---|",
    ]
    total = {"lf": 0, "lh": 0, "fnf": 0, "fnh": 0, "brf": 0, "brh": 0}
    for d in sorted(grouped):
        s = sums(grouped[d])
        for k in total:
            total[k] += s[k]
        out.append(
            "| {} | {} | {} | {} | {}/{} | {}/{} | {}/{} |".format(
                d, pct(s["lh"], s["lf"]), pct(s["fnh"], s["fnf"]), pct(s["brh"], s["brf"]),
                s["lh"], s["lf"], s["fnh"], s["fnf"], s["brh"], s["brf"],
            )
        )
    out.append(
        "| **TOTAL** | {} | {} | {} | {}/{} | {}/{} | {}/{} |".format(
            pct(total["lh"], total["lf"]), pct(total["fnh"], total["fnf"]), pct(total["brh"], total["brf"]),
            total["lh"], total["lf"], total["fnh"], total["fnf"], total["brh"], total["brf"],
        )
    )
    out.append("")
    if n_other:
        out.append("ملفات خارج `crates/*` مستثناة من الجدول: {}".format(n_other))
        out.append("")
    return "\n".join(out) + "\n"


_PUB_FN_RE = re.compile(r"^\s*pub(?:\s+(?:async|const|unsafe))*\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)")


def scan_pub_fns(src_root, crate):
    base = Path(src_root) / crate / "src"
    found = []
    if not base.is_dir():
        return found
    for path in sorted(base.glob("**/*.rs")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            m = _PUB_FN_RE.match(ln)
            if m:
                found.append((path.as_posix(), i, m.group(1)))
    return found


def fn_short(name):
    # llvm-cov lcov FNDA names are demangled paths (a::b::fn or fn.llvm.<hash>);
    # keep the last segment and drop the llvm hash suffix if present.
    short = name.split("::")[-1].strip()
    return re.sub(r"\.llvm\.[0-9A-Fa-f]+$", "", short)


def uncovered_pub_fns(crate_files, src_root, crate):
    pubs = scan_pub_fns(src_root, crate)
    zero = []
    for fc in crate_files:
        for name, cnt in fc.fnda.items():
            if cnt == 0:
                s = fn_short(name)
                if s:
                    zero.append(s)
    entries = set()
    matched = set()
    for s in zero:
        for f, ln, fname in pubs:
            if fname == s:
                matched.add(s)
                entries.add((f, ln, s))
    entries = sorted(entries, key=lambda e: (e[0], e[1], e[2]))
    unmatched = len(set(zero) - matched)
    return entries, unmatched


def _branch_section(crate_files):
    recs = []
    for fc in crate_files:
        for ln, _block, _branch, taken in fc.brda:
            if taken in ("0", "-"):  # 0 = not taken, "-" = unknown (both uncovered)
                recs.append((fc.sf, ln))
    if not recs:
        return ["- uncovered branches: none found (لا فروع غير مغطاة، أو لا BRDA في التقرير)"]
    per_line = {}
    for f, ln in recs:
        per_line[(f, ln)] = per_line.get((f, ln), 0) + 1
    keys = sorted(per_line, key=lambda k: (k[0], int(k[1]) if k[1].isdigit() else 10 ** 9))
    files_order = []
    for f, _ in keys:
        if f not in files_order:
            files_order.append(f)
    out = ["- uncovered branches: {} BRDA records on {} lines in {} files:".format(
        len(recs), len(keys), len(files_order))]
    shown = 0
    for f in files_order:
        fkeys = [k for k in keys if k[0] == f]
        out.append("  - `{}` — {}".format(f, sum(per_line[k] for k in fkeys)))
        for k in fkeys:
            if shown >= BRDA_CAP:
                break
            out.append("    - `{}:{}` ({})".format(f, k[1], per_line[k]))
            shown += 1
        if shown >= BRDA_CAP:
            break
    if shown < len(keys):
        out.append("  - …and {} more lines (cap {})".format(len(keys) - shown, BRDA_CAP))
    return out


def build_details(grouped, priority_arg, src_root):
    prio = normalize_priority(priority_arg)
    prio_matched = [d for d in grouped if is_priority_dir(d, prio)]
    prio_matched.sort(key=lambda d: (
        prio.index(strip_pkg_prefix(d)) if strip_pkg_prefix(d) in prio else len(prio), d))
    order = prio_matched + sorted(d for d in grouped if d not in prio_matched)
    out = [
        "## تفاصيل التغطية (coverage details) — §4a",
        "",
        "الدوال العامة غير المغطاة (uncovered `pub fn`، من FNDA count=0 مع مطابقة نصية) لكل crate —",
        "حزم المفسّرات (priority) أولًا — ثم الفروع غير المغطاة (uncovered BRDA) لحزم المفسّرات فقط.",
        "",
    ]
    for d in order:
        fcs = grouped[d]
        entries, unmatched = uncovered_pub_fns(fcs, src_root, d)
        out.append("### crate `{}`".format(d))
        out.append("")
        if entries:
            out.append("- uncovered `pub fn`: {}".format(len(entries)))
            for f, ln, s in entries[:FNDA_CAP]:
                out.append("  - `{}:{}` — `{}`".format(f, ln, s))
            if len(entries) > FNDA_CAP:
                out.append("  - …and {} more (cap {})".format(len(entries) - FNDA_CAP, FNDA_CAP))
        else:
            out.append("- uncovered `pub fn`: none found (لا توجد دوال عامة غير مغطاة، أو لا مطابقة نصية)")
        if unmatched:
            out.append("- zero-coverage FNDA entries with no textual `pub fn` match: {} (closures / non-pub items)".format(unmatched))
        if is_priority_dir(d, prio):
            out.extend(_branch_section(fcs))
        out.append("")
    return "\n".join(out) + "\n"


SAMPLE_LCOV = """TN:
SF:crates/oci/src/lib.rs
FN:10,oci::parse_manifest
FN:20,oci::parse_ref
FN:30,oci::internal_helper
FNDA:1,oci::parse_manifest
FNDA:0,oci::parse_ref
FNDA:0,oci::internal_helper
LF:14
LH:9
FNF:3
FNH:1
BRDA:10,0,0,1
BRDA:10,0,1,0
BRDA:12,1,0,-
BRF:3
BRH:1
DA:1,1
DA:2,1
DA:3,0
DA:4,1
DA:5,1
DA:6,0
DA:7,1
DA:8,1
DA:9,1
DA:10,1
DA:11,1
DA:12,1
DA:13,0
DA:14,1
end_of_record
SF:crates/volume-format/src/header.rs
FN:5,volume_format::read_header
FNDA:0,volume_format::read_header
LF:5
LH:5
FNF:1
FNH:0
DA:1,1
DA:2,1
DA:3,1
DA:4,1
DA:5,1
end_of_record
SF:crates/kernel-policy/src/lib.rs
DA:1,1
DA:2,0
end_of_record
SF:src/main.rs
LF:2
LH:2
DA:1,1
DA:2,1
end_of_record
SF:crates/oci/src/lib.rs
LF:2
LH:1
DA:1,1
DA:2,0
end_of_record
"""


def selftest():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "crates/oci/src").mkdir(parents=True)
        (root / "crates/volume-format/src").mkdir(parents=True)
        oci_src = "\n".join(
            ["// fake upstream source for --selftest (not real upstream code)"]
            + [""] * 8
            + ["pub fn parse_manifest() -> u32 { 1 }"]
            + [""] * 9
            + ["pub fn parse_ref() -> u32 { 2 }"]
        ) + "\n"
        (root / "crates/oci/src/lib.rs").write_text(oci_src, encoding="utf-8")
        (root / "crates/volume-format/src/header.rs").write_text(
            "\n\n\n\npub fn read_header() -> u32 { 3 }\n", encoding="utf-8")

        files = parse_lcov(SAMPLE_LCOV)
        assert len(files) == 4, "expected 4 merged SF records, got {}".format(len(files))
        grouped, other = aggregate(files)
        assert set(grouped) == {"oci", "volume-format", "kernel-policy"}, sorted(grouped)
        assert len(other) == 1, other

        s_oci = sums(grouped["oci"])
        assert (s_oci["lf"], s_oci["lh"]) == (14, 9), s_oci  # duplicate SF merged; explicit LF/LH win
        assert (s_oci["fnf"], s_oci["fnh"]) == (3, 1), s_oci
        assert (s_oci["brf"], s_oci["brh"]) == (3, 1), s_oci
        s_vf = sums(grouped["volume-format"])
        assert (s_vf["lf"], s_vf["lh"]) == (5, 5), s_vf
        assert (s_vf["fnf"], s_vf["fnh"]) == (1, 0), s_vf
        assert (s_vf["brf"], s_vf["brh"]) == (0, 0), s_vf
        s_kp = sums(grouped["kernel-policy"])
        assert (s_kp["lf"], s_kp["lh"]) == (2, 1), s_kp  # DA fallback (no LF/LH/FNF sections)

        assert pct(s_oci["lh"], s_oci["lf"]) == "64.3"
        assert pct(s_vf["fnh"], s_vf["fnf"]) == "0.0"
        assert pct(0, 0) == "n/a"

        summary = build_summary(grouped, len(other))
        assert "TOTAL" in summary and "64.3" in summary and "71.4" in summary  # TOTAL: 15/21 lines

        details = build_details(grouped, "ginux-oci,ginux-volume-format", str(root / "crates"))
        assert "crate `oci`" in details
        assert details.index("crate `oci`") < details.index("crate `volume-format`")  # priority order
        assert "crates/oci/src/lib.rs:20" in details and "parse_ref" in details
        assert "parse_manifest" not in details  # covered fn must NOT be listed
        assert "crates/volume-format/src/header.rs:5" in details and "read_header" in details
        assert "crates/oci/src/lib.rs:10" in details  # uncovered branch (taken=0)
        assert "crates/oci/src/lib.rs:12" in details  # uncovered branch (taken=-)
        assert "none found" in details  # volume-format has no BRDA section
    print("selftest: OK (feasibility-coverage)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="lcov.info → coverage summary/details markdown (v3.3 §4a)")
    ap.add_argument("lcov", nargs="?", help="path to the lcov.info tracefile")
    ap.add_argument("--src", default="crates", help="source root containing <crate>/src (default: crates)")
    ap.add_argument("--out", default="coverage-summary.md", help="summary markdown output path")
    ap.add_argument("--details", default="coverage-details.md", help="details markdown output path")
    ap.add_argument("--priority", default=PRIORITY_DEFAULT,
                    help="comma-separated priority crates (package or dir names)")
    ap.add_argument("--selftest", action="store_true", help="run the embedded hermetic selftest and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.lcov:
        ap.error("an lcov tracefile is required (or use --selftest)")
    files = parse_lcov(Path(args.lcov).read_text(encoding="utf-8", errors="replace"))
    grouped, other = aggregate(files)
    summary = build_summary(grouped, len(other))
    details = build_details(grouped, args.priority, args.src)
    Path(args.out).write_text(summary, encoding="utf-8")
    Path(args.details).write_text(details, encoding="utf-8")
    print("wrote {} ({} crates) and {} ({} files outside crates/ excluded)".format(
        args.out, len(grouped), args.details, len(other)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""feasibility-clippy.py — cargo clippy JSON → clippy::arithmetic_side_effects census (§4c).

Reads the stream emitted by `cargo clippy --message-format json` (one JSON object
per line; cargo's stderr progress lines mixed in are skipped), selects
compiler-message entries whose diagnostic code contains "arithmetic_side_effects",
dedupes by (file, line_start) using the primary span (falls back to spans[0]),
and writes arithmetic-sites.md: total distinct sites inside the parser crates
+ a per-file table. Sites outside --crates are counted as excluded, not listed.

Usage:
  python3 scripts/feasibility-clippy.py --json upstream/clippy.json \
      --out arithmetic-sites.md \
      --crates ginux-oci,ginux-protocol-state,ginux-volume-format

Selftest: python3 scripts/feasibility-clippy.py --selftest
Python3 stdlib only.
"""

import argparse
import json
import sys
from pathlib import Path

SITE_CAP = 100


def crate_dirs(crates_arg):
    """Package names (ginux-oci) and/or dir names (oci) → candidate crates/<dir> names."""
    dirs = []
    for c in (crates_arg or "").split(","):
        c = c.strip()
        if not c:
            continue
        d = c[len("ginux-"):] if c.startswith("ginux-") else c
        for cand in (d, c):
            if cand and cand not in dirs:
                dirs.append(cand)
    return dirs


def extract_arithmetic_sites(lines):
    """Return {(file, line_start): first rendered line} for arithmetic_side_effects diagnostics."""
    sites = {}
    for raw in lines:
        s = raw.strip()
        if not s.startswith("{"):
            continue
        try:
            obj = json.loads(s)
        except ValueError:
            continue
        if obj.get("reason") != "compiler-message":
            continue
        msg = obj.get("message") or {}
        code = (msg.get("code") or {}).get("code") or ""
        if "arithmetic_side_effects" not in code:
            continue
        spans = msg.get("spans") or []
        primary = next((sp for sp in spans if sp.get("is_primary")), spans[0] if spans else None)
        if not primary:
            continue
        fname = str(primary.get("file_name") or "")
        line_start = primary.get("line_start")
        if not fname or line_start is None:
            continue
        key = (fname, int(line_start))
        if key not in sites:
            rendered = (msg.get("rendered") or "").strip()
            sites[key] = rendered.splitlines()[0] if rendered else code
    return sites


def inside_crates(sites, dirs):
    def match(path):
        return any("/crates/{}/".format(d) in path or path.startswith("crates/{}/".format(d)) for d in dirs)
    return {k: v for k, v in sites.items() if match(k[0])}


def build_md(inside, n_excluded):
    out = [
        "## مواضع clippy::arithmetic_side_effects — parser crates (§4c)",
        "",
        "- إجمالي المواضع داخل الحزم المستهدفة (distinct sites): **{}**".format(len(inside)),
        "- مواضع خارجها (excluded, outside --crates): {}".format(n_excluded),
        "",
    ]
    if inside:
        per_file = {}
        for f, _l in inside:
            per_file[f] = per_file.get(f, 0) + 1
        out.append("| file | sites |")
        out.append("|---|---|")
        for f in sorted(per_file):
            out.append("| {} | {} |".format(f, per_file[f]))
        out.append("")
        keys = sorted(inside, key=lambda k: (k[0], k[1]))
        out.append("المواضع (file:line، cap {}):".format(SITE_CAP))
        for k in keys[:SITE_CAP]:
            out.append("- `{}:{}`".format(k[0], k[1]))
        if len(keys) > SITE_CAP:
            out.append("- …and {} more (cap {})".format(len(keys) - SITE_CAP, SITE_CAP))
    else:
        out.append("لا توجد مواضع (no arithmetic_side_effects sites found) — إمّا نظيفة، "
                   "أو لم يُصدَّر اللينت، أو المسارات خارج الحزم المستهدفة.")
    out.append("")
    out.append("### إعادة الإنتاج (reproduce)")
    out.append("")
    out.append("```")
    out.append("cargo clippy --package ginux-oci --package ginux-protocol-state \\")
    out.append("  --package ginux-volume-format --message-format json -- -W clippy::arithmetic_side_effects")
    out.append("```")
    return "\n".join(out) + "\n"


def _msg(code, spans, rendered):
    return json.dumps({"reason": "compiler-message",
                       "message": {"code": {"code": code}, "spans": spans, "rendered": rendered}})


def selftest():
    sample = "\n".join([
        _msg("clippy::arithmetic_side_effects",
             [{"file_name": "crates/oci/src/a.rs", "line_start": 42, "is_primary": True}],
             "warning: arithmetic operation that cannot panic"),
        _msg("clippy::arithmetic_side_effects",
             [{"file_name": "crates/oci/src/a.rs", "line_start": 42, "is_primary": True}],
             "warning: duplicate of the same site"),
        _msg("clippy::needless_borrow",
             [{"file_name": "crates/oci/src/a.rs", "line_start": 50, "is_primary": True}],
             "warning: needless borrow"),
        "Compiling ginux-oci v0.1.0",  # stderr noise line (not JSON) must be skipped
        _msg("clippy::arithmetic_side_effects",
             [{"file_name": "crates/protocol-state/src/p.rs", "line_start": 7, "is_primary": False},
              {"file_name": "crates/protocol-state/src/p.rs", "line_start": 9, "is_primary": True}],
             "warning: primary span fallback"),
        _msg("clippy::arithmetic_side_effects",
             [{"file_name": "crates/oci/src/a.rs", "line_start": 77, "is_primary": True}],
             "warning: another site"),
        _msg("clippy::arithmetic_side_effects",
             [{"file_name": "crates/other/src/o.rs", "line_start": 3, "is_primary": True}],
             "warning: outside the target crates"),
        '{"reason":"compiler-message","message":{"code":null,"spans":[]}}',  # no code → filtered
    ]) + "\n"
    sites = extract_arithmetic_sites(sample.splitlines())
    assert len(sites) == 4, sites  # 42 deduped; 50 filtered by code; 9, 77, other:3 kept
    dirs = crate_dirs("ginux-oci,ginux-protocol-state,ginux-volume-format")
    assert dirs == ["oci", "ginux-oci", "protocol-state", "ginux-protocol-state",
                    "volume-format", "ginux-volume-format"], dirs
    inside = inside_crates(sites, dirs)
    assert len(inside) == 3, inside
    assert ("crates/oci/src/a.rs", 42) in inside and ("crates/oci/src/a.rs", 77) in inside
    assert ("crates/protocol-state/src/p.rs", 9) in inside  # primary span fallback (not spans[0] @7)
    md = build_md(inside, len(sites) - len(inside))
    assert "| crates/oci/src/a.rs | 2 |" in md, md
    assert "crates/protocol-state/src/p.rs:9" in md, md
    assert "excluded, outside --crates): 1" in md, md
    print("selftest: OK (feasibility-clippy)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="cargo clippy JSON → arithmetic_side_effects census (v3.3 §4c)")
    ap.add_argument("--json", dest="json_path", help="path to the clippy.json stream")
    ap.add_argument("--out", default="arithmetic-sites.md")
    ap.add_argument("--crates", default="ginux-oci,ginux-protocol-state,ginux-volume-format")
    ap.add_argument("--selftest", action="store_true", help="run the embedded hermetic selftest and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.json_path:
        ap.error("--json is required (or use --selftest)")
    sites = extract_arithmetic_sites(
        Path(args.json_path).read_text(encoding="utf-8", errors="replace").splitlines())
    dirs = crate_dirs(args.crates)
    inside = inside_crates(sites, dirs)
    md = build_md(inside, len(sites) - len(inside))
    Path(args.out).write_text(md, encoding="utf-8")
    print("wrote {}: {} sites inside, {} excluded".format(args.out, len(inside), len(sites) - len(inside)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

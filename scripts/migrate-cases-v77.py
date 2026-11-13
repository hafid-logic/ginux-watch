#!/usr/bin/env python3
"""migrate-cases-v77.py — one-shot label migration per owner rulings (v7.7-4).

Owner decisions (v7.7 clause 4, 2026-11-13):
  1. Merge request + directed_at_us into for_us with a subtag preserving
     the provenance class (for_us_subtag: request | directed_at_us).
  2. dc-041 promoted status_of_others -> for_us (subtag: escalated).
  3. dc-005 noise confirmed (owner-ruled annotation).
  4. dc-032 needs_supervisor confirmed + rule T2-1 authorized (annotation).

Textual edits only: keeps every other byte of the YAML intact. Idempotent:
running twice makes no further change.
"""
import pathlib
import sys

CASES = pathlib.Path("eval/decider-cases/cases")
CHANGED = []


def patch(path, edits):
    txt = path.read_text(encoding="utf-8")
    orig = txt
    for old, new in edits:
        if new in txt:
            continue  # already applied (idempotent)
        assert old in txt, "%s: pattern missing: %r" % (path.name, old)
        txt = txt.replace(old, new, 1)
    if txt != orig:
        path.write_text(txt, encoding="utf-8")
        CHANGED.append(path.name)


def main() -> int:
    if not CASES.is_dir():
        print("run from repo root", file=sys.stderr)
        return 2
    for f in sorted(CASES.glob("dc-*.yaml")):
        txt = f.read_text(encoding="utf-8")
        if "\nfor_us_subtag:" in txt:
            continue
        if "\nt1_label: request\n" in txt:
            patch(f, [("t1_label: request",
                       "t1_label: for_us\nfor_us_subtag: request")])
        elif "\nt1_label: directed_at_us\n" in txt:
            patch(f, [("t1_label: directed_at_us",
                       "t1_label: for_us\nfor_us_subtag: directed_at_us")])
        elif f.stem == "dc-041":
            patch(f, [("t1_label: status_of_others",
                       "t1_label: for_us\nfor_us_subtag: escalated"),
                      ("for_us: false", "for_us: true"),
                      ("labeling_rationale:",
                       "labeling_rationale: [v7.7 مالك: رُقّيت إلى for_us — انتقال حالة خيط لنا زناد قاطع] ")])
        elif f.stem == "dc-005":
            patch(f, [("labeling_rationale:",
                       "labeling_rationale: [v7.7 مالك: noise مؤكدة — ALERT مزوّد ممتصّ لا يُعاد إنذاره] ")])
        elif f.stem == "dc-032":
            patch(f, [("labeling_rationale:",
                       "labeling_rationale: [v7.7 مالك: needs_supervisor مؤكدة + قاعدة T2-1 معتمدة] ")])
    print("patched: %d file(s): %s" % (len(CHANGED), ", ".join(CHANGED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

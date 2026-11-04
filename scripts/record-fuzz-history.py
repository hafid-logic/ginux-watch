#!/usr/bin/env python3
"""Append one row per fuzz target to reports/fuzz-history.md (v3.2 §1).

Input: round-results/results-<target>.txt key=value files produced by fuzz.yml.
Idempotent: a (run_id, target) pair is never appended twice. Creates the file
with a header if missing. Rows: date | trigger | upstream head | target |
seconds | execs | cov regions/lines/functions | crash artifacts | run url.
"""
import argparse
import pathlib
import re
import sys


def parse_results(path: pathlib.Path) -> dict:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r"^([a-z_]+)=(.*)$", line)
        if m:
            data[m.group(1)] = m.group(2)
            continue
        m2 = re.match(r"^regions (\S+) lines (\S+) functions (\S+)$", line)
        if m2:
            data["cov_regions"], data["cov_lines"], data["cov_functions"] = m2.groups()
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--history", required=True)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()

    results_dir = pathlib.Path(args.results_dir)
    files = sorted(results_dir.glob("results-*.txt"))
    if not files:
        print("no results files found; nothing to record", file=sys.stderr)
        return 0

    history = pathlib.Path(args.history)
    if history.exists():
        text = history.read_text(encoding="utf-8")
    else:
        text = (
            "# fuzz-history (v3.2 §1)\n\n"
            "One row per target per round. Columns: date (UTC) | trigger | upstream main head\n"
            "| target | seconds | execs | cov regions % | cov lines % | cov functions % |\n"
            "crash artifacts | run url.\n"
            "Column note (carried from run5 recipe): the last coverage column is named\n"
            "'functions' by llvm-cov TOTAL row field 13 but behaved as branch coverage in\n"
            "prior sessions — read comparatively, not absolutely.\n\n"
            "| date | trigger | head | target | seconds | execs | cov regions | cov lines | cov functions | crashes | run |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
        )

    appended = 0
    rows = []
    for f in files:
        d = parse_results(f)
        rows.append(d)

    # newest last: keep a stable order (target name)
    for d in sorted(rows, key=lambda x: x.get("target", "")):
        run_id = d.get("run_id", "n/a")
        target = d.get("target", "n/a")
        if run_id != "n/a":
            # idempotence: skip when this run_id already has a row for this target
            already = any(
                (f"| {target} |" in line) and (run_id in line)
                for line in text.splitlines()
            )
            if already:
                continue
        row = (
            f"| {args.date} | {d.get('trigger', 'n/a')} | {d.get('upstream_sha', 'n/a')[:8]} "
            f"| {target} | {d.get('seconds', 'n/a')} | {d.get('execs', 'n/a')} "
            f"| {d.get('cov_regions', 'n/a')} | {d.get('cov_lines', 'n/a')} "
            f"| {d.get('cov_functions', 'n/a')} | {d.get('crash_artifacts', 'n/a')} "
            f"| {d.get('run_url', 'n/a')} |"
        )
        if not text.endswith("\n"):
            text += "\n"
        text += row + "\n"
        appended += 1

    if appended:
        history.write_text(text, encoding="utf-8")
    print(f"appended {appended} row(s) to {args.history}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

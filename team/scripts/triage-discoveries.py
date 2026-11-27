#!/usr/bin/env python3
"""triage-discoveries — smart screening bridge (owner directive 2026-11-28).
Reads state/discoveries.json (surviving cargo-mutants lines) + CURRENT
origin/main sources, groups live survivors by (crate, file, function),
excludes display/format/cosmetic mutants, requires >=2 live survivors in the
same function whose names are not already covered by an existing test fn,
prioritizes boundary/logic/bitmask/match-arm mutations in high-value crates,
and emits state/author-candidates.json with full fn_source for each of the
top 15 candidates. Read-only: no builds, no cargo, no network beyond git fetch."""
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/triage-upstream")
TOP = 15
PRIORITY_CRATES = ["ginux-process", "ginux-vfs", "ginux-instance",
                   "ginux-kernel-views", "ginux-oci"]
# cosmetic / out-of-scope patterns (policy: display/format mutants rejected)
EXCLUDE_FN = re.compile(r"\b(fmt|display|debug|render|describe|label|name_of)\b", re.I)
EXCLUDE_LINE = re.compile(
    r"(replace .*fmt|write!|format!|Display|Debug|-> &str with|-> String with"
    r"|with \"\"|with \"x\"|delete field .*name)", re.I)
# high-value mutation shapes
BOUNDARY = re.compile(r"replace (<|<=|>|>=) with")
LOGIC = re.compile(r"replace (\|\||&&|==|!=) with")
BITMASK = re.compile(r"replace (&|\||\^|<<|>>) with")
MATCHARM = re.compile(r"delete match arm")
GUARD = re.compile(r"(replace .* with (true|false)\b|delete !|replace ! )")
RETVAL = re.compile(r"replace .* -> .* with (Ok\(|Err\(|Some\(|None|0\b|1\b|-1\b|true|false)")

LINE_RE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<desc>.*)$")
FN_TAIL = re.compile(r"\bin\s+(?P<fn>[A-Za-z0-9_:<>]+)\s*$")


def ensure_clone():
    if not (U / ".git").exists():
        subprocess.run(["git", "clone", "--quiet",
                        "https://github.com/gmkurtzer/ginux.git", str(U)], check=True)
    subprocess.run(["git", "-C", str(U), "fetch", "-q", "origin", "main"], check=True)


def show(path):
    r = subprocess.run(["git", "-C", str(U), "show", "origin/main:" + path],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def fn_span(src_lines, line_no):
    """Find the enclosing fn for a 1-based line: scan upward for the nearest
    fn signature, then brace-walk to its end. Returns (name, start, end)."""
    i = min(line_no, len(src_lines)) - 1
    sig = None
    while i >= 0:
        m = re.search(r"\bfn\s+([a-zA-Z0-9_]+)", src_lines[i])
        if m and "//" not in src_lines[i].split("fn")[0]:
            sig = (m.group(1), i)
            break
        i -= 1
    if sig is None:
        return None
    name, start = sig
    depth = 0; opened = False
    j = start
    while j < len(src_lines):
        for ch in src_lines[j]:
            if ch == "{":
                depth += 1; opened = True
            elif ch == "}":
                depth -= 1
                if opened and depth == 0:
                    return name, start + 1, j + 1
        j += 1
    return name, start + 1, len(src_lines)


def score(descs, crate):
    s = 0
    for d in descs:
        if BOUNDARY.search(d): s += 4
        if LOGIC.search(d): s += 3
        if BITMASK.search(d): s += 3
        if MATCHARM.search(d): s += 3
        if GUARD.search(d): s += 2
        if RETVAL.search(d): s += 1
    if crate in PRIORITY_CRATES:
        s += 5 * (len(PRIORITY_CRATES) - PRIORITY_CRATES.index(crate))
    return s


def main():
    ensure_clone()
    disc = json.loads((ROOT / "state/discoveries.json").read_text())
    groups = {}
    dropped = {"cosmetic": 0, "stale-line": 0, "no-fn": 0, "covered": 0}
    src_cache = {}
    for crate, blob in disc.get("crates", {}).items():
        for raw in blob.get("survivors", []):
            m = LINE_RE.match(raw.strip())
            if not m:
                continue
            rel, line, desc = m["file"], int(m["line"]), m["desc"]
            fm = FN_TAIL.search(desc)
            fn_hint = fm["fn"].split("::")[-1] if fm else None
            if EXCLUDE_LINE.search(desc) or (fn_hint and EXCLUDE_FN.search(fn_hint)):
                dropped["cosmetic"] += 1; continue
            path = rel if rel.startswith("crates/") else f"crates/{crate}/src/{rel}"
            if path not in src_cache:
                s = show(path)
                src_cache[path] = s.split("\n") if s else None
            lines = src_cache[path]
            if lines is None or line > len(lines):
                dropped["stale-line"] += 1; continue
            span = fn_span(lines, line)
            if span is None:
                dropped["no-fn"] += 1; continue
            fname, start, end = span
            if EXCLUDE_FN.search(fname):
                dropped["cosmetic"] += 1; continue
            # JIT liveness: the referenced line must still contain code relevant
            # to the mutation (non-empty, non-comment) — cheap textual check.
            target = lines[line - 1].strip()
            if not target or target.startswith("//"):
                dropped["stale-line"] += 1; continue
            key = (crate, path, fname)
            g = groups.setdefault(key, {"start": start, "end": end, "mutants": []})
            g["mutants"].append({"line": line, "desc": desc, "source_line": target})
    # coverage: skip functions already exercised by a test naming them
    candidates = []
    for (crate, path, fname), g in groups.items():
        if len(g["mutants"]) < 2:
            continue
        lines = src_cache[path]
        tests_region = "\n".join(lines)  # whole file: test fns live in mod tests
        covered = re.search(r"fn\s+[a-z0-9_]*" + re.escape(fname) + r"[a-z0-9_]*\s*\(", tests_region)
        # count occurrences: definition itself is 1; a test mentioning the name adds more
        defs = len(re.findall(r"\bfn\s+" + re.escape(fname) + r"\b", tests_region))
        calls_in_tests = len(re.findall(r"\b" + re.escape(fname) + r"\s*\(", tests_region))
        if covered and (defs > 1 or calls_in_tests > defs + 2):
            dropped["covered"] += 1; continue
        fn_source = "\n".join(lines[g["start"] - 1:g["end"]])
        candidates.append({
            "crate": crate, "file": path, "function": fname,
            "span": [g["start"], g["end"]],
            "live_mutants": len(g["mutants"]),
            "score": score([m["desc"] for m in g["mutants"]], crate),
            "mutants": g["mutants"],
            "fn_source": fn_source,
        })
    candidates.sort(key=lambda c: (-c["score"], -c["live_mutants"], c["function"]))
    out = {
        "generated_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
        "main_sha": subprocess.run(["git", "-C", str(U), "rev-parse", "origin/main"],
                                   capture_output=True, text=True).stdout.strip(),
        "total_survivors": disc.get("total_survivors"),
        "dropped": dropped,
        "candidates": candidates[:TOP],
    }
    (ROOT / "state/author-candidates.json").write_text(json.dumps(out, indent=1))
    print(f"candidates: {len(candidates)} (top {TOP} written); dropped: {dropped}")
    for c in candidates[:TOP]:
        print(f"  {c['score']:3d} {c['crate']:20s} {c['function']:40s} x{c['live_mutants']}")


if __name__ == "__main__":
    main()

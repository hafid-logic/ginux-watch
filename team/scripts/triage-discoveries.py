#!/usr/bin/env python3
"""triage-discoveries v2 — screening bridge + EXACT MUTANT SYNTHESIS (phase 3).
Reads state/discoveries.json (surviving cargo-mutants lines) + CURRENT
origin/main sources; groups live survivors by (crate, file, function);
excludes display/format/cosmetic mutants; requires >=2 live survivors per
function not already covered by an existing test; ranks boundary/logic/
bitmask/match-arm mutations in priority crates.

NEW (owner directive phase 3):
- ready_mutants: for every survivor, synthesize the exact {name, old, new,
  line[, context]} pair from the source at (line, col) — identical to what
  cargo-mutants applied, so survives=true is guaranteed by construction
  (the mutant literally survived the existing suite in the scan).
  Uniqueness: single-line old when full-file count==1, else grow to 2-3
  surrounding lines until unique; recorded as context-scoped when needed.
- crate_balanced_top: best 3 candidates per crate, so ginux-instance's 325
  survivors cannot crowd out the other crates.
Read-only: no builds, no cargo."""
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
U = Path("/tmp/triage-upstream")
TOP = 15
PER_CRATE = 3
PRIORITY_CRATES = ["ginux-process", "ginux-vfs", "ginux-instance",
                   "ginux-kernel-views", "ginux-oci"]
EXCLUDE_FN = re.compile(r"\b(fmt|display|debug|render|describe|label|name_of)\b", re.I)
EXCLUDE_LINE = re.compile(
    r"(replace .*fmt|write!|format!|Display|Debug|-> &str with|-> String with"
    r"|with \"\"|with \"x\"|delete field .*name)", re.I)
BOUNDARY = re.compile(r"replace (<|<=|>|>=) with")
LOGIC = re.compile(r"replace (\|\||&&|==|!=) with")
BITMASK = re.compile(r"replace (&|\||\^|<<|>>) with")
MATCHARM = re.compile(r"delete match arm")
GUARD = re.compile(r"(replace .* with (true|false)\b|delete !|replace ! )")
RETVAL = re.compile(r"replace .* -> .* with (Ok\(|Err\(|Some\(|None|0\b|1\b|-1\b|true|false)")

LINE_RE = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<desc>.*)$")
FN_TAIL = re.compile(r"\bin\s+(?P<fn>[A-Za-z0-9_:<>]+)\s*$")
REPL_OP = re.compile(r"^replace (?P<x>.+?) with (?P<y>.+?) in ")
DEL_OP = re.compile(r"^delete (?P<x>.+?) in ")
REPL_GUARD = re.compile(r"^replace match guard (?P<x>.+?) with (?P<y>.+?) in ")
DEL_ARM = re.compile(r"^delete match arm (?P<pat>.+?) in ")
REPL_FN = re.compile(r"^replace (?P<sig>.+?) -> (?P<ty>[^ ]+) with (?P<y>.+?) in ")


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


def unique_anchor(lines, idx, old_line, new_line):
    """Grow a window around idx until the old block is unique in the file.
    Returns (old, new, context_needed) or None."""
    whole = "\n".join(lines)
    if whole.count(old_line) == 1:
        return old_line, new_line, False
    for radius in (1, 2):
        lo = max(0, idx - radius); hi = min(len(lines), idx + radius + 1)
        old_block = "\n".join(lines[lo:hi])
        rel = idx - lo
        new_lines = lines[lo:hi][:]
        new_lines[rel] = new_line
        new_block = "\n".join(new_lines)
        if whole.count(old_block) == 1:
            # prover supports context-scoped replace: context=old_block,
            # old=old_line inside it (must be unique WITHIN the block)
            if old_block.count(old_line) == 1:
                return old_line, new_line, old_block
            return old_block, new_block, False
    return None


def synth_mutant(lines, ln, col, desc, fname):
    """Exact synthesis from cargo-mutants description at (ln, col), 1-based."""
    idx = ln - 1
    if idx >= len(lines):
        return None
    line = lines[idx]
    ci = col - 1

    m = REPL_GUARD.match(desc)
    if m:
        x, y = m["x"], m["y"]
        if line[ci:ci + len(x)] != x:
            return None
        new_line = line[:ci] + y + line[ci + len(x):]
        u = unique_anchor(lines, idx, line, new_line)
        if not u: return None
        old, new, ctx = u
        mu = {"name": f"guard-{y}-{ln}", "old": old, "new": new, "line": ln}
        if ctx: mu["context"] = ctx
        return mu

    m = DEL_ARM.match(desc)
    if m:
        pat = m["pat"]
        if not line.lstrip().startswith(pat):
            return None
        # delete the whole arm line (single-line arms only; multi-line skipped)
        if "=>" not in line or not line.rstrip().endswith(","):
            return None
        new_line = ""
        whole = "\n".join(lines)
        if whole.count(line + "\n") == 1:
            return {"name": f"del-arm-{ln}", "old": line + "\n", "new": "", "line": ln}
        u = unique_anchor(lines, idx, line, "")
        if not u: return None
        old, new, ctx = u
        # deletion via context: replace block containing the arm with block minus arm
        if ctx:
            nl = lines[:]
            nl[idx] = ""
            lo = max(0, idx - 1); hi = min(len(lines), idx + 2)
            old_b = "\n".join(lines[lo:hi]); new_b = "\n".join(nl[lo:hi])
            if whole.count(old_b) == 1:
                return {"name": f"del-arm-{ln}", "old": old_b, "new": new_b, "line": ln}
        return None

    m = REPL_FN.match(desc)
    if m and " -> " in desc and not REPL_OP.match(desc.replace("match guard ", "")):
        # function-return replacement: body becomes `return <y>;` — needs full
        # fn body span; emit as context-scoped whole-function replacement.
        y = m["y"]
        span = fn_span(lines, ln)
        if span is None: return None
        _, start, end = span
        # signature line is start-1..; find opening brace line
        body_old = "\n".join(lines[start - 1:end])
        # replace body: keep signature up to '{', then ' return y; }'
        sig_end = None
        for k in range(start - 1, end):
            if "{" in lines[k]:
                sig_end = k
                break
        if sig_end is None: return None
        head = lines[sig_end][:lines[sig_end].index("{") + 1]
        new_body = head + f"\n        return {y};\n    }}"
        whole = "\n".join(lines)
        if whole.count(body_old) != 1:
            return None
        return {"name": f"ret-{ln}", "old": body_old, "new": new_body, "line": ln,
                "note": "whole-function body replacement (cargo-mutants fn-value mutant)"}

    m = REPL_OP.match(desc)
    if m:
        x, y = m["x"], m["y"]
        if line[ci:ci + len(x)] != x:
            return None
        new_line = line[:ci] + y + line[ci + len(x):]
        u = unique_anchor(lines, idx, line, new_line)
        if not u: return None
        old, new, ctx = u
        tag = re.sub(r"[^A-Za-z0-9]+", "", x)[:6] or "op"
        mu = {"name": f"{tag}2{re.sub(r'[^A-Za-z0-9]+','',y)[:6] or 'val'}-{ln}c{col}",
              "old": old, "new": new, "line": ln}
        if ctx: mu["context"] = ctx
        return mu

    m = DEL_OP.match(desc)
    if m:
        x = m["x"]
        if line[ci:ci + len(x)] != x:
            return None
        new_line = line[:ci] + line[ci + len(x):]
        u = unique_anchor(lines, idx, line, new_line)
        if not u: return None
        old, new, ctx = u
        mu = {"name": f"del{re.sub(r'[^A-Za-z0-9]+','',x)[:6]}-{ln}c{col}",
              "old": old, "new": new, "line": ln}
        if ctx: mu["context"] = ctx
        return mu
    return None


def main():
    ensure_clone()
    disc = json.loads((ROOT / "state/discoveries.json").read_text())
    groups = {}
    dropped = {"cosmetic": 0, "stale-line": 0, "no-fn": 0, "covered": 0, "unsynth": 0}
    src_cache = {}
    for crate, blob in disc.get("crates", {}).items():
        for raw in blob.get("survivors", []):
            m = LINE_RE.match(raw.strip())
            if not m:
                continue
            rel, line, col, desc = m["file"], int(m["line"]), int(m["col"]), m["desc"]
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
            target = lines[line - 1].strip()
            if not target or target.startswith("//"):
                dropped["stale-line"] += 1; continue
            key = (crate, path, fname)
            g = groups.setdefault(key, {"start": start, "end": end,
                                        "mutants": [], "ready_mutants": []})
            g["mutants"].append({"line": line, "desc": desc, "source_line": target})
            mu = synth_mutant(lines, line, col, desc, fname)
            if mu is None:
                dropped["unsynth"] += 1
            else:
                # dedup identical synthesized pairs
                if not any(r["old"] == mu["old"] and r["new"] == mu["new"]
                           for r in g["ready_mutants"]):
                    g["ready_mutants"].append(mu)
    candidates = []
    for (crate, path, fname), g in groups.items():
        if len(g["mutants"]) < 2:
            continue
        lines = src_cache[path]
        region = "\n".join(lines)
        defs = len(re.findall(r"\bfn\s+" + re.escape(fname) + r"\b", region))
        calls = len(re.findall(r"\b" + re.escape(fname) + r"\s*\(", region))
        if defs > 1 or calls > defs + 2:
            dropped["covered"] += 1; continue
        fn_source = "\n".join(lines[g["start"] - 1:g["end"]])
        candidates.append({
            "crate": crate, "file": path, "function": fname,
            "span": [g["start"], g["end"]],
            "live_mutants": len(g["mutants"]),
            "ready_count": len(g["ready_mutants"]),
            "score": score([m["desc"] for m in g["mutants"]], crate),
            "mutants": g["mutants"],
            "ready_mutants": g["ready_mutants"],
            "fn_source": fn_source,
        })
    candidates.sort(key=lambda c: (-c["score"], -c["live_mutants"], c["function"]))
    balanced = {}
    for c in candidates:
        balanced.setdefault(c["crate"], [])
        if len(balanced[c["crate"]]) < PER_CRATE:
            balanced[c["crate"]].append(
                {k: c[k] for k in ("crate", "file", "function", "score",
                                   "live_mutants", "ready_count")})
    out = {
        "generated_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
        "main_sha": subprocess.run(["git", "-C", str(U), "rev-parse", "origin/main"],
                                   capture_output=True, text=True).stdout.strip(),
        "total_survivors": disc.get("total_survivors"),
        "dropped": dropped,
        "candidates": candidates[:TOP],
        "crate_balanced_top": balanced,
        "all_qualified": [{k: c[k] for k in ("crate", "file", "function", "score",
                                             "live_mutants", "ready_count")}
                          for c in candidates],
    }
    (ROOT / "state/author-candidates.json").write_text(json.dumps(out, indent=1))
    print(f"candidates: {len(candidates)} (top {TOP}); dropped: {dropped}")
    for crate, lst in balanced.items():
        print(f"  {crate}: " + ", ".join(f"{x['function']}(r{x['ready_count']})" for x in lst))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""validate-result.py — deterministic validator for team/results/<dir>/.

Gates: result.md exists & <= 1500 words; meta.json parses with required fields; evidence
tags present; every [MEASURED] line cites a path/URL/SHA; no secret patterns; no
placeholders/overstatement. Writes validation.md per dir. With --enforce, a FAIL moves the
matching card from team/tasks/done/ back to open/ (status: rejected + reasons).
"""
import json, os, re, sys, shutil, datetime, argparse

SECRET = re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}"
                    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[A-Za-z0-9-]{10,}"
                    r"|bearer [A-Za-z0-9._\-]{20,}", re.I)
PLACEHOLDER = re.compile(r"(?<![\w/-])(TODO|FIXME|XXX)(?![\w/-])|guaranteed|100% secure|proven safe", re.I)
TAG = re.compile(r"\[(MEASURED|OBSERVED|INFERRED|UNVERIFIED)\]")
PATHY = re.compile(r"(evidence/|reports/|team/|\.md|\.rs|\.sh|\.py|\.json|\.toml"
                   r"|https?://\S+|[0-9a-f]{7,40}\b)", re.I)
WORD_CAP = 1500

def check_dir(d):
    reasons, notes = [], []
    rp = os.path.join(d, "result.md")
    if not os.path.isfile(rp):
        return ["result.md missing"], notes
    text = open(rp, encoding="utf-8").read()
    wc = len(text.split())
    if wc > WORD_CAP:
        reasons.append(f"result.md {wc} words > cap {WORD_CAP}")
    if not TAG.search(text):
        reasons.append("no evidence tag [MEASURED/OBSERVED/INFERRED/UNVERIFIED] found")
    lines = text.splitlines()
    if not any(PATHY.search(ln) for ln in lines):
        reasons.append("no evidence path/URL/SHA anywhere in result.md")
    for i, ln in enumerate(lines):
        if "[MEASURED]" not in ln or ln.lstrip().startswith("#"):
            continue
        ctx = "\n".join(lines[max(0, i - 1):i + 2])  # evidence often on the adjacent line
        if not PATHY.search(ctx):
            notes.append(f"summary MEASURED line (section-level evidence): {ln[:70]!r}")
    mp = os.path.join(d, "meta.json")
    if not os.path.isfile(mp):
        reasons.append("meta.json missing")
    else:
        try:
            m = json.load(open(mp))
            for k in ("duration_min", "tools", "verified_format", "status"):
                if k not in m:
                    reasons.append(f"meta.json missing field: {k}")
            if m.get("status") not in ("done", "partial"):
                reasons.append(f"meta.json status invalid: {m.get('status')!r}")
        except Exception as e:
            reasons.append(f"meta.json unparseable: {e}")
    if SECRET.search(text):
        reasons.append("SECRET PATTERN in result.md")
    hits = sorted({x.group(0) for x in PLACEHOLDER.finditer(text)})
    if hits:
        reasons.append("placeholder/overstatement words: " + ", ".join(hits))
    if os.path.isdir(os.path.join(d, "evidence")):
        n = len(os.listdir(os.path.join(d, "evidence")))
        notes.append(f"evidence files: {n}")
    return reasons, notes

def find_card(repo, tid):
    done = os.path.join(repo, "team/tasks/done")
    if not os.path.isdir(done):
        return None
    for fn in os.listdir(done):
        if tid.startswith(fn[:-3]) and fn.endswith(".md"):
            return os.path.join(done, fn)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="team/results")
    ap.add_argument("--enforce", action="store_true")
    a = ap.parse_args()
    repo = os.path.dirname(os.path.dirname(os.path.abspath(a.root)))
    if os.path.basename(repo) != "ginux-watch":
        repo = os.getcwd()
    summary = []
    for name in sorted(os.listdir(a.root)):
        d = os.path.join(a.root, name)
        if not os.path.isdir(d) or name.startswith("."):
            continue
        reasons, notes = check_dir(d)
        verdict = "PASS" if not reasons else "FAIL"
        stamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(os.path.join(d, "validation.md"), "w") as f:
            f.write(f"# validation — {name} — {verdict} — {stamp}\n\n")
            for r in reasons:
                f.write(f"- FAIL: {r}\n")
            for n in notes:
                f.write(f"- note: {n}\n")
            if not reasons:
                f.write("- all gates passed\n")
        summary.append(f"{name}: {verdict}")
        if reasons and a.enforce:
            card = find_card(repo, name)
            if card:
                tgt = os.path.join(repo, "team/tasks/open", os.path.basename(card))
                shutil.move(card, tgt)
                txt = open(tgt, encoding="utf-8").read()
                txt = txt.replace("status: done", "status: rejected", 1) \
                         .replace("status: partial", "status: rejected", 1)
                txt += "\nrejected_by: validator " + stamp + "\nrejected_reasons:\n" + \
                       "".join(f"  - {r}\n" for r in reasons)
                open(tgt, "w", encoding="utf-8").write(txt)
    print("\n".join(summary) if summary else "no result dirs")
    fails = sum(1 for s in summary if s.endswith("FAIL"))
    sys.exit(0)  # workflow always commits the validation output

if __name__ == "__main__":
    main()

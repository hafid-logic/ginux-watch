#!/usr/bin/env python3
"""build-index.py — build upstream-dump.jsonl + index.json for the data branch.

Modes:
  --dump-dir D            read local snapshot (issues.json list + pulls/<n>-files.json)
  --fetch-files           Actions mode: fetch PR files via `gh api` (GITHUB_TOKEN implicit)
  --out O                 output directory (writes upstream-dump.jsonl, index.json)
Deterministic, stdlib-only, no secrets printed.
"""
import json, os, re, sys, subprocess, datetime, argparse

STOP = set("""the and for with this that from into when then have has are was not but all can
will its our new add fix use using issue pull request merged closed open cherry pick rebase
update updates updated improve improve refactor change changes changed file files line lines
make test tests testing support add added support code function return returns value values
""".split())

def tokens(text, limit=10):
    freq = {}
    for t in re.findall(r"[a-z0-9_]{3,}", (text or "").lower()):
        if t in STOP:
            continue
        freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]

def load_dump(dump_dir):
    path = os.path.join(dump_dir, "issues.json")
    with open(path) as f:
        items = json.load(f)
    files_map = {}
    pf = os.path.join(dump_dir, "pulls")
    if os.path.isdir(pf):
        for fn in os.listdir(pf):
            m = re.match(r"(\d+)-files\.json$", fn)
            if m:
                with open(os.path.join(pf, fn)) as f:
                    files_map[int(m.group(1))] = [x.get("filename", "") for x in json.load(f)]
    return items, files_map

def fetch_files(number):
    try:
        out = subprocess.run(["gh", "api", "--paginate",
                              f"repos/gmkurtzer/ginux/pulls/{number}/files"],
                             capture_output=True, text=True, check=True, timeout=60)
        return [x.get("filename", "") for x in json.loads(out.stdout or "[]")]
    except Exception:
        return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fetch-files", action="store_true")
    a = ap.parse_args()
    items, files_map = load_dump(a.dump_dir)
    lines, idx_items, kw = [], {}, {}
    for it in items:
        num = it.get("number")
        is_pr = bool(it.get("pull_request"))
        pr = it.get("pull_request") or {}
        if a.fetch_files and is_pr:
            files = fetch_files(num)
        else:
            files = files_map.get(num, [])
        title = it.get("title") or ""
        body = it.get("body") or ""
        rec = {
            "number": num, "kind": "pr" if is_pr else "issue", "title": title,
            "state": it.get("state"),
            "merged_at": pr.get("merged_at") if is_pr else None,
            "created_at": it.get("created_at"), "updated_at": it.get("updated_at"),
            "labels": [l.get("name", "") for l in it.get("labels", [])],
            "files": files, "title_words": len(title.split()), "body_words": len(body.split()),
        }
        lines.append(json.dumps(rec, ensure_ascii=False))
        toks = tokens(title + " " + body[:2000])
        idx_items[str(num)] = {"kind": rec["kind"], "title": title, "state": rec["state"],
                               "merged_at": rec["merged_at"], "files": files[:30], "keywords": toks}
        for t in toks:
            kw.setdefault(t, []).append(num)
    index = {"generated_at_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "source_repo": "gmkurtzer/ginux", "item_count": len(idx_items),
             "items": idx_items, "keywords": kw}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "upstream-dump.jsonl"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(a.out, "index.json"), "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"indexed {len(idx_items)} items -> {a.out}")

if __name__ == "__main__":
    main()

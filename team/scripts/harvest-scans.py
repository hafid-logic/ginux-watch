#!/usr/bin/env python3
"""harvest-scans.py — v9.3: keep the discovery stock full automatically.

Downloads missed.txt from every successful mutation-scan run and rewrites
state/discoveries.json. Event-driven: fired by workflow_run on mutation-scan
completion, so stock refills the moment a scan finishes (no cron wait).

Artifact download 302-redirects to blob storage; forwarding Authorization breaks
it (playbook D10) -> capture Location, then fetch WITHOUT auth headers.
"""
import datetime, io, json, os, sys, urllib.error, urllib.request, zipfile, pathlib

REPO = os.environ.get("GITHUB_REPOSITORY", "hafid-logic/ginux-watch")
TOK = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
AH = {"Authorization": "Bearer " + TOK, "User-Agent": "harvest",
      "Accept": "application/vnd.github+json"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OP = urllib.request.build_opener(NoRedirect)


def gj(p):
    with urllib.request.urlopen(urllib.request.Request("https://api.github.com" + p, headers=AH), timeout=30) as r:
        return json.load(r)


def missed_lines(run_id):
    out = []
    for a in gj(f"/repos/{REPO}/actions/runs/{run_id}/artifacts").get("artifacts", []):
        loc = None
        try:
            OP.open(urllib.request.Request(a["archive_download_url"], headers=AH), timeout=25)
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location")
        if not loc:
            continue
        with urllib.request.urlopen(urllib.request.Request(loc, headers={"User-Agent": "harvest"}), timeout=40) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        crate = a["name"].replace("mutation-scan-", "")
        for n in z.namelist():
            if n.endswith("missed.txt"):
                for line in z.read(n).decode(errors="replace").splitlines():
                    if line.strip():
                        out.append((crate, line.strip()))
    return out


def main():
    runs = gj(f"/repos/{REPO}/actions/workflows/mutation-scan.yml/runs?per_page=30").get("workflow_runs", [])
    per, seen = {}, set()
    for r in runs:
        if r.get("conclusion") != "success":
            continue
        for crate, line in missed_lines(r["id"]):
            if line in seen:
                continue
            seen.add(line)
            per.setdefault(crate, []).append(line)
    doc = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "source": "mutation-scan artifacts (cargo-mutants missed.txt)",
           "total_survivors": sum(len(v) for v in per.values()),
           "crates": {k: sorted(v) for k, v in sorted(per.items())}}
    pathlib.Path("state").mkdir(exist_ok=True)
    pathlib.Path("state/discoveries.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"harvest: {doc['total_survivors']} survivors across {len(per)} crates")
    return 0


if __name__ == "__main__":
    sys.exit(main())

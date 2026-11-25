#!/usr/bin/env python3
"""reserve-proposals — attach a pre-filled PR title+body (English, GFM, AI footer)
to every PUSHED reserve as a one-click GitHub compare URL. Reads PR.title+PR.md
from approved/pending/c8-<name>/. Writes outbox/RESERVES.md + state/reserves.json.
Token: GH_TOKEN or PIPELINE_PAT. Never opens a PR (opening is always human)."""
import json, os, subprocess, urllib.request, urllib.parse, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def cfg():
    c={}
    for line in (ROOT/"config/pipeline-autopilot.yml").read_text().splitlines():
        line=line.split("#")[0].strip()
        if ":" in line:
            k,v=line.split(":",1); c[k.strip()]=v.strip()
    return c
def api(tok, path):
    req=urllib.request.Request("https://api.github.com"+path,
        headers={"Authorization":"Bearer "+tok,"Accept":"application/vnd.github+json","User-Agent":"reserve-proposals"})
    return json.load(urllib.request.urlopen(req, timeout=30))
def proposal_url(up, fo, branch, title, body):
    q=urllib.parse.urlencode({"quick_pull":"1","title":title,"body":body}, quote_via=urllib.parse.quote_plus)
    return f"https://github.com/{up}/compare/main...{fo}:{branch}?{q}"
def main():
    c=cfg(); up=c["upstream"]; fork=c["fork"]; prefix=c["branch_prefix"]; stock=c["stock_dir"]
    fo=fork.split("/")[0]
    tok=os.environ.get("GH_TOKEN") or os.environ.get("PIPELINE_PAT")
    if not tok:
        tok=subprocess.run(["gh","auth","token"],capture_output=True,text=True).stdout.strip()
    opened={p["head"]["ref"] for p in api(tok,f"/repos/{up}/pulls?state=open&per_page=100") if p["user"]["login"]==c["author"]}
    pushed=[b["name"] for b in api(tok,f"/repos/{fork}/branches?per_page=100") if b["name"].startswith(prefix)]
    rows=[]
    for b in pushed:
        if b in opened: continue
        try:
            if api(tok,f"/repos/{up}/compare/main...{fo}:{b}").get("ahead_by",0)<=0: continue
        except Exception: continue
        d=ROOT/stock/("c8-"+b[len(prefix):])
        tf=d/"PR.title"; bf=d/"PR.md"
        if not (tf.exists() and bf.exists()): continue
        title=tf.read_text().strip(); body=bf.read_text()
        rows.append({"branch":b,"title":title,"url":proposal_url(up,fo,b,title,body)})
    out={"generated_utc":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"reserves":rows}
    (ROOT/"state/reserves.json").write_text(json.dumps(out,indent=1))
    md=["# Reserves ready for owner to open (one click, pre-filled title+body)","",
        "Opening upstream is ALWAYS human. Each link opens GitHub's PR form pre-filled (English, GFM, AI footer). No manual copying.",""]
    for r in rows:
        md += [f"## `{r['branch']}`", f"**Title:** {r['title']}", f"[Open pre-filled PR]({r['url']})", ""]
    (ROOT/"outbox").mkdir(exist_ok=True)
    (ROOT/"outbox/RESERVES.md").write_text("\n".join(md))
    print(f"reserves with proposals: {len(rows)}")
    for r in rows: print(" -",r["branch"])
if __name__=="__main__": main()

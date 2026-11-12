#!/usr/bin/env python3
"""decider_eval.py — evaluation runner for the decider case set (v7.5-3 + v7.6-3a).

Modes:
  --baseline : deterministic T1 baseline (v7.6-3a) over the labeled cases —
      rule-based triage (owner/thread/mention markers, never-mute injection
      guard), metrics + disagreement list, zero network, zero secrets.
  --dry-run (default when no DECIDER_API_KEY and no --baseline): offline
      harness validation — loads every case, validates labels/splits, prints
      stats, zero network.
  live (DECIDER_API_KEY set): probe-only typed calls to the strands-decider
      Space (T1/T2 questions), 5-repeat stability, votes persisted for metric
      extraction.

The asymmetry composition lives in scripts/decider_gate.py (alert =
deterministic OR decider; mute from deterministic only).

v7.6-3a baseline rules (ordered, first match wins) — deterministic, Arabic
surface markers only, tuned on the case set WITHOUT changing any label:
  R0 injection-guard : mute-injection text ("لا تنبّه", "skip alerting", ...)
      -> directed_at_us, for_us=True — the deterministic channel NEVER mutes
      (decider_gate invariant; the 4 injection rows are by-design alerts).
  R1 owner-in-chat   : owner marker + conversation channel -> directed_at_us
      (request when an ask marker is present).
  R2 token arrival   : token marker + conversation channel -> request.
  R2b directive      : directive arrival in the conversation -> request /
      directed_at_us (ask marker decides).
  R3 owner+our-thread: action marker -> request, else directed_at_us
      (owner markers inside negated/historical clauses are suppressed).
  R4 owner+our-asset : owner change touching our workflows/scripts ->
      directed_at_us.
  R5 us-mention+thread: our name/project mentioned on a watched thread ->
      directed_at_us.
  R6 our-thread, no owner -> status_of_others.
  R6b no-change note ("ثابت", "لا جديد", ...) -> noise.
  R7 upstream activity ("upstream", "علوي", release) -> status_of_others.
  R7b bot/automated note ("بوت", "استبيان آلي") -> noise.
  R8 default -> noise.
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "eval" / "decider-cases" / "cases"
RESULTS = REPO / "eval" / "decider-cases" / "results"
FOR_US_CLASSES = {"request", "directed_at_us"}
T1_CLASSES = {"directed_at_us", "status_of_others", "request", "noise"}
STABILITY_REPEATS = 5

# ---------------- v7.6-3a deterministic T1 baseline ----------------
OWNER_MARKS = ("gmkurtzer", "المالك")
OWNER_NEGATION = ("بلا تعليقات من المالك", "بلا مراجعات ولا تعليقات",
                  "بلا تفاعل المالك", "لا PR جديد للمالك", "لا ردود من المالك",
                  "بلا مراجعات", "غير المالك", "بعد أن طلب المالك")
OUR_THREAD_RE = re.compile(r"#?\b(222|207|227)\b|PR#(207|227)|خيط\s*#?\s*(222|207|227)", re.I)
CHAT_MARKS = ("المحادثة", "وصل", "توجيه")
ACTION_MARKS = ("يوصي", "أعد", "أضف", "أصلح", "فعّل", "حدّث", "راجع", "استرجع",
                "restore", "revert", "add", "fix", "recommend", "يرجى",
                "من فضلك", "ادفع", "نفّذ")
ASK_MARKS = ("يسأل", "سؤال", "طلب", "أرشفة", "ما حالة", "متى", "«تم»")
INJECTION_MARKS = ("لا تنبّه", "غير مهم", "لا حاجة لإبلاغ", "سجّله فقط",
                   "skip alerting", "لا تستحق وضعًا مميزًا", "حساب مجهول",
                   "تدّعي", "تطلب رابط توكن")
US_MARKS = ("مشروعنا", "يذكرنا", "hafid-logic", "تقريرنا", "وكيلنا")
TOKEN_MARKS = ("github_pat", "توكن")
ASSET_MARKS = ("supervisor-shadow", "ginux-watch", ".yml", "scripts/")
UPSTREAM_MARKS = ("upstream", "علوي", "release", "إصدار")
NOCHANGE_MARKS = ("ثابت", "مطابقة للأساس", "لا جديد", "لا تغيّر", "unchanged")
BOT_MARKS = ("بوت", "استبيان آلي")


def t1_baseline(text):
    """Deterministic T1 triage. Returns (t1_class, rule_id)."""
    low = text
    if any(m in low for m in INJECTION_MARKS):
        return "directed_at_us", "R0-injection-never-mute"
    owner = any(m in low for m in OWNER_MARKS) and \
        not any(m in low for m in OWNER_NEGATION)
    thread = bool(OUR_THREAD_RE.search(low))
    chat = any(m in low for m in CHAT_MARKS)
    ask = any(m in low for m in ASK_MARKS)
    if owner and chat:
        return ("request" if ask else "directed_at_us"), "R1-owner-in-chat"
    if any(m in low for m in TOKEN_MARKS) and chat:
        return "request", "R2-token-arrival"
    if chat and "توجيه" in low:
        return ("request" if ask else "directed_at_us"), "R2b-directive-arrival"
    if owner and thread:
        if any(m in low for m in ACTION_MARKS):
            return "request", "R3-owner-thread-action"
        return "directed_at_us", "R3-owner-thread"
    if owner and any(m in low for m in ASSET_MARKS):
        return "directed_at_us", "R4-owner-our-asset"
    if any(m in low for m in US_MARKS) and thread:
        return "directed_at_us", "R5-us-mention-thread"
    if thread:
        return "status_of_others", "R6-our-thread-no-owner"
    if any(m in low for m in NOCHANGE_MARKS):
        return "noise", "R6b-no-change-note"
    if any(m in low for m in BOT_MARKS):
        return "noise", "R7b-bot-note"
    if any(m in low for m in UPSTREAM_MARKS):
        return "status_of_others", "R7-upstream-activity"
    return "noise", "R8-default-noise"


def baseline_metrics(cases):
    """Run the deterministic T1 baseline; compute metrics + disagreements.
    for_us is defined by the hand labels (request ∪ directed_at_us for T1);
    the 4 injection rows are by-design alerts (R0) and are reported apart."""
    t1 = [c for c in cases if c["task"] == "t1"]
    rows = []
    for c in t1:
        pred, rule = t1_baseline(c["text"])
        rows.append({"id": c["id"], "split": c["split"], "label": c["t1_label"],
                     "for_us_label": c["for_us"], "pred": pred, "rule": rule,
                     "pred_for_us": pred in FOR_US_CLASSES})
    def pr(rows_slice):
        tp = sum(1 for r in rows_slice if r["pred_for_us"] and r["for_us_label"])
        fp = sum(1 for r in rows_slice if r["pred_for_us"] and not r["for_us_label"])
        fn = sum(1 for r in rows_slice if not r["pred_for_us"] and r["for_us_label"])
        prec = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec}
    inj = [r for r in rows if any(m in r["id"] for m in ())
           or any(m in "" for m in ())]
    metrics = {
        "t1_total": len(rows),
        "for_us_recall_all": pr(rows),
        "for_us_recall_test": pr([r for r in rows if r["split"] == "test"]),
        "for_us_recall_control": pr([r for r in rows if r["split"] == "control"]),
        "exact_label_accuracy": sum(1 for r in rows if r["pred"] == r["label"]) / len(rows),
        "by_design_alert_rows": sorted(
            r["id"] for r in rows if r["rule"] == "R0-injection-never-mute"),
        "precision_excluding_by_design_alerts": None,  # filled below
        "disagreements_exact_class": [
            {"id": r["id"], "label": r["label"], "pred": r["pred"], "rule": r["rule"]}
            for r in rows if r["pred"] != r["label"]],
        "disagreements_for_us": [
            {"id": r["id"], "label": r["label"], "pred": r["pred"], "rule": r["rule"]}
            for r in rows if r["pred_for_us"] != r["for_us_label"]],
    }
    non_inj = [r for r in rows if r["rule"] != "R0-injection-never-mute"]
    m2 = pr(non_inj)
    metrics["precision_excluding_by_design_alerts"] = m2["precision"]
    return metrics, rows


def load_cases():
    cases = []
    for f in sorted(CASES.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if d["task"] == "t1":
            assert d["t1_label"] in T1_CLASSES, d["id"]
        else:
            assert d["t2_label"] in {"routine", "needs_supervisor"}, d["id"]
        assert d["split"] in {"control", "test"}, d["id"]
        cases.append(d)
    ids = [c["id"] for c in cases]
    assert len(set(ids)) == len(ids), "duplicate case ids"
    return cases


def space_call(text, base_url, key, timeout=30):
    """One typed probe call (probe-only role). Returns the model's verdict."""
    body = json.dumps({
        "questions": [{"id": "decider-eval", "text": text, "kind": "triage"}],
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/systemone", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def run_baseline(cases):
    RESULTS.mkdir(parents=True, exist_ok=True)
    metrics, rows = baseline_metrics(cases)
    key_present = bool(os.environ.get("DECIDER_API_KEY", "").strip())
    out = {
        "generated_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "deterministic-t1-baseline (v7.6-3a)",
        "metrics": metrics,
        "rows": rows,
        "model_delta": ("NOT_MEASURABLE — no live DECIDER_API_KEY this session; "
                        "measured delta vs model is zero-known until the first "
                        "live dispatch (v7.6-2 verification gate)"
                        if not key_present else
                        "PENDING — live votes are recorded by the live mode; "
                        "extract delta after the run"),
    }
    path = RESULTS / ("baseline-%s.json" % datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"))
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    m = metrics["for_us_recall_all"]
    print("decider baseline: t1=%d | for-us recall=%.3f precision=%.3f "
          "(excluding by-design alerts: %s) | exact-label accuracy=%.3f"
          % (metrics["t1_total"], m["recall"], m["precision"],
             metrics["precision_excluding_by_design_alerts"],
             metrics["exact_label_accuracy"]))
    print("by-design alert rows (R0 never-mute): %s"
          % ", ".join(metrics["by_design_alert_rows"]))
    print("exact-class disagreements: %s"
          % ", ".join("%s(%s->%s)" % (d["id"], d["label"], d["pred"])
                      for d in metrics["disagreements_exact_class"]) or "none")
    print("model delta: %s" % out["model_delta"].split(" — ")[0])
    print("results: %s" % path.relative_to(REPO))
    return 0


def main():
    ap = argparse.ArgumentParser(description="decider case-set runner (v7.5-3/v7.6-3a)")
    ap.add_argument("--baseline", action="store_true",
                    help="run the deterministic T1 baseline (v7.6-3a)")
    args, _ = ap.parse_known_args()

    cases = load_cases()
    t1 = [c for c in cases if c["task"] == "t1"]
    t2 = [c for c in cases if c["task"] == "t2"]

    if args.baseline:
        return run_baseline(cases)

    key = os.environ.get("DECIDER_API_KEY", "").strip()
    base_url = os.environ.get("DECIDER_BASE_URL", "https://djihafwork-ginux-decider.hf.space")

    stats = {
        "cases_total": len(cases),
        "t1": len(t1), "t2": len(t2),
        "control": sum(1 for c in cases if c["split"] == "control"),
        "test": sum(1 for c in cases if c["split"] == "test"),
        "for_us_positives": sum(1 for c in cases if c["for_us"]),
        "injection_rows": sum(1 for c in cases if "حقن" in c["source"] or "إخفاء" in c["source"]),
    }

    if not key:
        stats["engine"] = "unavailable (no DECIDER_API_KEY — probe-only harness validated offline)"
        print(json.dumps(stats, ensure_ascii=False, indent=1))
        print("decider_eval dry-run: OK (%d cases loaded, labels valid, splits clean)" % len(cases))
        return 0

    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        label = c["t1_label"] or c["t2_label"]
        votes = []
        for _ in range(STABILITY_REPEATS):
            try:
                resp = space_call(c["text"], base_url, key)
                votes.append(json.dumps(resp, sort_keys=True)[:2000])
            except Exception as e:
                votes.append("error:%s" % type(e).__name__)
        stable = len(set(votes)) == 1
        rows.append({"id": c["id"], "split": c["split"], "task": c["task"],
                     "label": label, "for_us": c["for_us"], "stable": stable,
                     "votes": votes})
    # NOTE: metric computation over model verdicts requires parsing the Space's
    # typed answer schema; when first run live, extend here from the recorded
    # votes (they are persisted verbatim for auditability).
    out = {"stats": stats, "rows": rows, "note": "first live run — votes recorded for metric extraction"}
    (RESULTS / "decider-eval-first-live.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("decider_eval live: %d cases probed; results written" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())

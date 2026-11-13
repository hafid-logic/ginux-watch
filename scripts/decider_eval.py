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
  v7.7-4 owner rulings (2026-11-13): R0 standing (never mute from a content
      channel); request/directed_at_us merged into for_us with provenance
      subtag; R9 hold-breach (our thread + owner-requested hold + head
      movement -> for_us[escalated], dc-041 ruling); T2-1 success claim
      without independent evidence -> needs_supervisor (dc-032 ruling).
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
FOR_US_CLASSES = {"for_us"}
T1_CLASSES = {"for_us", "status_of_others", "noise"}
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
# v7.7-4: R9 (dc-041 promotion) + T2-1 (dc-032 ruling) marker sets.
HOLD_MARKS = ("إمساك", "hold")
HEAD_MOVE_MARKS = ("تغيّر", "تحرك", "head", "رأس")
SUCCESS_MARKS = ("تم بنجاح", "بنجاح", "خضراء", "green", "success")
NEG_EVIDENCE_MARKS = ("بلا sha", "بلا تحقق", "بدون sha", "بدون تحقق",
                      "بلا دليل", "بدون دليل", "no sha", "without")
EVIDENCE_MARKS = ("sha", "ls-remote", "raw", "measured", "assert", "schema",
                  "rev-parse", "ff فوق", "18/18")


def t1_baseline(text):
    """Deterministic T1 triage (v7.7-4). Returns (t1_class, rule_id, subtag).

    R0 is a standing rule (owner-confirmed v7.7): a content-channel mute is
    never honored. The provenance subtag preserves what the pre-merge
    taxonomy would have said (request | directed_at_us | escalated)."""
    low = text
    if any(m in low for m in INJECTION_MARKS):
        return "for_us", "R0-injection-never-mute", "directed_at_us"
    owner = any(m in low for m in OWNER_MARKS) and \
        not any(m in low for m in OWNER_NEGATION)
    thread = bool(OUR_THREAD_RE.search(low))
    chat = any(m in low for m in CHAT_MARKS)
    ask = any(m in low for m in ASK_MARKS)
    if owner and chat:
        return "for_us", "R1-owner-in-chat", ("request" if ask else "directed_at_us")
    if any(m in low for m in TOKEN_MARKS) and chat:
        return "for_us", "R2-token-arrival", "request"
    if chat and "توجيه" in low:
        return "for_us", "R2b-directive-arrival", ("request" if ask else "directed_at_us")
    if owner and thread:
        if any(m in low for m in ACTION_MARKS):
            return "for_us", "R3-owner-thread-action", "request"
        return "for_us", "R3-owner-thread", "directed_at_us"
    if owner and any(m in low for m in ASSET_MARKS):
        return "for_us", "R4-owner-our-asset", "directed_at_us"
    if any(m in low for m in US_MARKS) and thread:
        return "for_us", "R5-us-mention-thread", "directed_at_us"
    if thread and any(m in low for m in HOLD_MARKS) \
            and any(m in low for m in HEAD_MOVE_MARKS):
        return "for_us", "R9-hold-breach", "escalated"
    if thread:
        return "status_of_others", "R6-our-thread-no-owner", None
    if any(m in low for m in NOCHANGE_MARKS):
        return "noise", "R6b-no-change-note", None
    if any(m in low for m in BOT_MARKS):
        return "noise", "R7b-bot-note", None
    if any(m in low for m in UPSTREAM_MARKS):
        return "status_of_others", "R7-upstream-activity", None
    return "noise", "R8-default-noise", None


def t2_baseline(text):
    """Deterministic T2 baseline v0 (v7.7-4): rule T2-1 only.

    T2-1 (owner-authorized, dc-032 ruling): a success claim with no
    independent evidence -> needs_supervisor. Negated evidence markers
    ("بلا sha", "بلا تحقق") count as absence, and last_success is stripped
    so heartbeat fields never read as success claims. Expansion pending
    further owner rulings; the default stays routine."""
    low = text.replace("last_success", "")
    if not any(m in low for m in SUCCESS_MARKS):
        return "routine", "T2-default-routine"
    if any(m in low for m in NEG_EVIDENCE_MARKS) \
            or not any(m in low for m in EVIDENCE_MARKS):
        return "needs_supervisor", "T2-1-success-claim-no-evidence"
    return "routine", "T2-success-with-evidence"


def baseline_metrics(cases):
    """Run the deterministic T1 baseline; compute metrics + disagreements.
    for_us is the merged owner class (v7.7: ex-request ∪ ex-directed_at_us,
    provenance kept in for_us_subtag); the 4 injection rows are by-design
    alerts (R0) and are reported apart."""
    t1 = [c for c in cases if c["task"] == "t1"]
    rows = []
    for c in t1:
        pred, rule, subtag = t1_baseline(c["text"])
        rows.append({"id": c["id"], "split": c["split"], "label": c["t1_label"],
                     "for_us_label": c["for_us"], "pred": pred, "rule": rule,
                     "subtag": subtag, "label_subtag": c.get("for_us_subtag"),
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
    fu_rows = [r for r in rows if r["label"] == "for_us"]
    sub_ok = sum(1 for r in fu_rows if r["subtag"] == r["label_subtag"])
    metrics["subtag_accuracy"] = {
        "agreement": (sub_ok / len(fu_rows)) if fu_rows else None,
        "n": len(fu_rows),
        "mismatches": [{"id": r["id"], "subtag": r["subtag"],
                        "label_subtag": r["label_subtag"]}
                       for r in fu_rows if r["subtag"] != r["label_subtag"]],
    }
    t2_rows = []
    for c in [c for c in cases if c["task"] == "t2"]:
        pred, rule = t2_baseline(c["text"])
        t2_rows.append({"id": c["id"], "split": c["split"],
                        "label": c["t2_label"], "pred": pred, "rule": rule})
    metrics["t2"] = {
        "total": len(t2_rows),
        "exact_accuracy": (sum(1 for r in t2_rows if r["pred"] == r["label"])
                           / len(t2_rows)) if t2_rows else None,
        "t2_1_rows": [r["id"] for r in t2_rows
                      if r["rule"] == "T2-1-success-claim-no-evidence"],
        "t2_1_false_fires": [r["id"] for r in t2_rows
                             if r["rule"] == "T2-1-success-claim-no-evidence"
                             and r["label"] != "needs_supervisor"],
        "rows": t2_rows,
    }
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
        "mode": "deterministic-t1+T2-1-baseline (v7.7-4)",
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
    print("subtag accuracy: %.3f (n=%d) | T2 exact accuracy: %.3f "
          "| T2-1 rows: %s (false fires: %s)"
          % (metrics["subtag_accuracy"]["agreement"],
             metrics["subtag_accuracy"]["n"], metrics["t2"]["exact_accuracy"],
             ",".join(metrics["t2"]["t2_1_rows"]) or "none",
             ",".join(metrics["t2"]["t2_1_false_fires"]) or "none"))
    print("model delta: %s" % out["model_delta"].split(" — ")[0])
    print("results: %s" % path.relative_to(REPO))
    return 0


def main():
    ap = argparse.ArgumentParser(description="decider case-set runner (v7.5-3/v7.6-3a)")
    ap.add_argument("--baseline", action="store_true",
                    help="run the deterministic T1+T2-1 baseline (v7.7-4)")
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

#!/usr/bin/env python3
"""v7.4 clause 2 — output-length distribution (p95) of the NINE shadow proposals
and the derived max_tokens = p95 x 1.5 (directive v7.4-2).

Population: the exact nine shadow proposals compared in reports/shadow-compare.md
(20261108-0007Z-s52, 20261108-1830Z-s56, 20261108-1927Z, 20261108-2211Z,
20261109-0208Z, 20261109-2226Z, 20261110-0006Z, 20261110-0007Z,
20261110-0011Z) — the same list the shadow-compare table calls "9 proposals".

Measured units:
  - words: whitespace tokens of the rendered .md view (the same source
    shadow-compare.md used) [MEASURED];
  - tokens: tiktoken cl100k_base over the report object serialized compactly
    (json.dumps, ensure_ascii=False). The model's own tokenizer differs; this
    is a documented PROXY [INFERRED: tokenizer proxy, +-10% typical for
    English JSON].

Also derives attempt-1 numbers of the 20261110-0011Z nvidia truncation:
the archived raw reply (eval/failures/2026-11-10/rerun-0011Z.nvidia.
truncated_json.txt) gives visible-content tokens; completion hit the 3000
cap (finish_reason=length), so reasoning ~= cap - content [INFERRED].
Attempt 2 (compressed retry) usage is [MEASURED] in state/llm-status.json
shadow.last_attempt.usage_summary (completion_tokens=3000,
reasoning_tokens=2499, finish_reason=length).

Output: JSON to stdout (also written next to this script when -o given).
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # eval/nvidia-truncation -> repo root
SHADOW = ROOT / "shadow"
FAIL = ROOT / "eval" / "failures" / "2026-11-10"

NINE = ["20261108-0007Z-s52.openrouter", "20261108-1830Z-s56.openrouter",
        "20261108-1927Z-shadow.google-ai-studio", "20261108-2211Z-shadow.google-ai-studio",
        "20261109-0208Z-shadow.google-ai-studio", "20261109-2226Z-shadow.google-ai-studio",
        "20261110-0006Z-shadow.google-ai-studio", "20261110-0007Z-shadow.google-ai-studio",
        "20261110-0011Z-shadow.google-ai-studio"]

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def n_tok(s):
        return len(_enc.encode(s))
except Exception:  # pragma: no cover - fallback if tiktoken missing offline
    def n_tok(s):
        return max(1, math.ceil(len(s) / 4.0))  # chars/4 heuristic


def p95(vals):
    """Linear-interpolation p95 (numpy 'linear' method)."""
    v = sorted(vals)
    if len(v) == 1:
        return v[0]
    k = 0.95 * (len(v) - 1)
    f = math.floor(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (k - f) * (v[c] - v[f])


def wc(s):
    return len(s.split())


def main():
    rows = []
    word_counts, tok_counts = [], []
    for rid in NINE:
        p = SHADOW / ("%s.json" % rid)
        d = json.loads(p.read_text(encoding="utf-8"))
        rep = d["report"]
        # compact serialization = closest guess at what the model emitted
        compact = json.dumps(rep, ensure_ascii=False, separators=(",", ":"))
        words = sum(wc(rep.get(k) and " ".join(map(str, rep.get(k))) or "")
                    for k in ("strengths", "weaknesses", "risks", "next_items"))
        words += sum(wc(" ".join(str(x) for x in (
            c.get("claim", ""), c.get("evidence_tag", ""), c.get("verdict", ""))))
            for c in rep.get("claims_checked", []))
        words += sum(wc(" ".join(str(x) for x in (
            c.get("open_point", ""), c.get("decision", ""), c.get("rationale", ""))))
            for c in rep.get("decisions", []))
        toks = n_tok(compact)
        word_counts.append(words)
        tok_counts.append(toks)
        rows.append({"id": rid, "words": words, "tokens_proxy": toks})

    p95_w = p95(word_counts)
    p95_t = p95(tok_counts)
    max_tokens_new = math.ceil(p95_t * 1.5)

    # per-field maxima across the nine outputs (basis for word caps)
    fields_max = {}
    for rid in NINE:
        rep = json.loads((SHADOW / ("%s.json" % rid)).read_text(
            encoding="utf-8"))["report"]
        for arr in ("strengths", "weaknesses", "risks", "next_items"):
            m = max((wc(x) for x in rep.get(arr, [])), default=0)
            fields_max[arr] = max(fields_max.get(arr, 0), m)
            fields_max[arr + "#len"] = max(fields_max.get(arr + "#len", 0),
                                           len(rep.get(arr, [])))
        for c in rep.get("claims_checked", []):
            for k in ("claim",):
                fields_max["claims_checked." + k] = max(
                    fields_max.get("claims_checked." + k, 0), wc(c.get(k, "")))
        for c in rep.get("decisions", []):
            for k in ("open_point", "decision", "rationale"):
                fields_max["decisions." + k] = max(
                    fields_max.get("decisions." + k, 0), wc(c.get(k, "")))
        fields_max["claims_checked#len"] = max(
            fields_max.get("claims_checked#len", 0), len(rep.get("claims_checked", [])))
        fields_max["decisions#len"] = max(
            fields_max.get("decisions#len", 0), len(rep.get("decisions", [])))

    # attempt-1 derivation (20261110-0011Z nvidia, initial attempt)
    att1 = {"artifact": "eval/failures/2026-11-10/rerun-0011Z.nvidia.truncated_json.txt"}
    raw1 = (FAIL / "rerun-0011Z.nvidia.truncated_json.txt").read_text(
        encoding="utf-8", errors="replace")
    att1["finish_reason"] = "length"          # [MEASURED] v7.3 record + state
    att1["max_tokens_cap"] = 3000             # config then in force
    att1["visible_content_tokens_proxy"] = n_tok(raw1)
    att1["reasoning_tokens_inferred"] = max(0, 3000 - att1["visible_content_tokens_proxy"])
    att1["note"] = ("per-attempt usage was not persisted at call time (state "
                    "usage_summary holds the RETRY call because meta2 overwrote "
                    "meta); content tokens = tiktoken proxy over the committed "
                    "artifact [MEASURED artifact / INFERRED decomposition]")

    out = {
        "generated": "2026-11-10",
        "population": "nine shadow proposals (shadow-compare.md list)",
        "rows": rows,
        "p95_words": round(p95_w, 1),
        "p95_tokens_proxy": round(p95_t, 1),
        "max_tokens_new": max_tokens_new,
        "formula": "max_tokens = ceil(p95_tokens_proxy * 1.5) (directive v7.4-2)",
        "tokenizer": "tiktoken cl100k_base [INFERRED proxy for nemotron tokenizer]",
        "fields_max_observed": fields_max,
        "attempt1_0011Z": att1,
        "attempt2_0011Z_measured": {
            "finish_reason": "length",
            "completion_tokens": 3000,
            "reasoning_tokens": 2499,
            "source": "state/llm-status.json shadow.last_attempt.usage_summary",
        },
    }
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if "-o" in sys.argv:
        (Path(__file__).parent / "p95-analysis-2026-11-10.json").write_text(
            txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()

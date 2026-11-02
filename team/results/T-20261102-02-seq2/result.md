# T-20261102-02-seq2 — duplicate gate P11–P17 vs updated snapshot (v2.2 re-claim)

Run: sequential pass, worker w4s, 2026-11-02T22:33–22:40Z. Inputs used only: `work/data-wt/index.json`, `work/data-wt/upstream-dump.jsonl`, `work/upstream-dump/issues.json` (card-listed backup, for issue bodies only), read-only clone `work/ginux` (origin/main = `95f8ef2447f52eacd1b73e8612465fcd38bcc31b` [MEASURED] via `git log --oneline -1 origin/main`). No prior run results read; no network, no gh, no builds.

## Freshness gate

[MEASURED] `index.json` field `generated_at_utc = "2026-11-02T22:05:39Z"`, `item_count = 56` (command: `python3 -c "json.load(...); print(d['generated_at_utc'], d['item_count'])"`). Checked at 2026-11-02T22:33:40Z (`date -u`) → age ≈ 0.47 h < 26 h → snapshot FRESH; no STALE-INDEX verdicts. Dump has 56 records (`wc -l` style count in python: 56) — matches.

## Verdicts

- **P11** — DUPLICATE (#5). 
- **P12** — FIXED (merged PR #9, merge commit `c921e98d4955bda72de203836436e7a951eb94eb`).
- **P13** — FIXED (merged PR #9, merge commit `c921e98d…`; ledger commit `339149da79575dcbf76136c9ffe2f7315f9fb6a7` on main).
- **P14** — NOT-DUPLICATE (query `(?i)\b(cow|copy[-_ ]?on[-_ ]?write|fork)\b` → 0/56).
- **P15** — NOT-DUPLICATE (query `(?i)\b(provenance|supervision|steering|ai-generated|generated code)\b` → 0/56).
- **P16** — NOT-DUPLICATE (query `(?i)\bunsafe\b` → 1 hit #9; examined, root-cause mismatch).
- **P17** — NOT-DUPLICATE (query `(?i)(26\.7|\bbaseline\b)` → 2 hits #7,#8; filename-only, root-cause mismatch).

## Per-row evidence

**P11 (giant file: cpu.rs 44,324 lines).** [MEASURED] Snapshot item `index.json:items["5"]` = open issue "Tracking: technical criticism of Ginux collected from public reviews". [OBSERVED] Its body (backup `work/upstream-dump/issues.json`, #5) contains the exact root cause: "`kernel/src/arch/x86_64/cpu.rs` is 44,324 lines and holds non-arch Linux personality policy" (Stage F5). [MEASURED] Query `(?i)\b(refactor|split|monolithic|giant|file size|too large|oversized)\b` over titles+keywords → 0 hits among #42–#56; #56 touches `cpu.rs` only for TSC clock work. [MEASURED] Not fixed: `git show origin/main:kernel/src/arch/x86_64/cpu.rs | wc -l` = 42,752 at `95f8ef24`. Root cause persists upstream → DUPLICATE (#5).

**P12 (docs contradiction: "green" gates vs declared failure).** [MEASURED] Snapshot #9 (pr, merged 2026-10-31T16:01:51Z) file list includes `.github/workflows/check.yml`. [MEASURED] Merge commit `c921e98d…` is reachable from origin/main (`git log --merges --oneline origin/main` shows "Merge pull request #9"). [MEASURED] `git show origin/main:.github/workflows/check.yml` begins `name: check`. The root cause (no CI, known-failing test gate) is remediated on main → FIXED.

**P13 (compat ledger "Complete" incl. ENOSYS stubs).** [MEASURED] Snapshot #9 file list includes `docs/LINUX-COMPATIBILITY.md` (25 files, identical in index.json and upstream-dump.jsonl record #9). [MEASURED] `git show --stat 339149da…` = "Correct Linux compatibility status semantics", docs/LINUX-COMPATIBILITY.md 31 insertions/30 deletions; `git merge-base --is-ancestor 339149da origin/main` → true. [MEASURED] `git show origin/main:docs/LINUX-COMPATIBILITY.md | grep -c "Unsupported"` = 19 at `95f8ef24`. [OBSERVED] Snapshot/dump record #11 (same commit message) as closed with no merged_at — noting the index gap; the content is on main via #9's merge lineage. → FIXED.

**P14 (COW disabled for forks, declared design debt).** [MEASURED] Query `(?i)\b(cow|copy[-_ ]?on[-_ ]?write|fork)\b` over title+keywords+files of all 56 items → 0 hits. Negative result recorded → NOT-DUPLICATE.

**P15 (modularity risk of AI-generated code, 23%).** [MEASURED] Query `(?i)\b(provenance|supervision|steering|ai-generated|generated code)\b` → 0/56 (loose substring pass had over-matched; corrected with word boundaries). → NOT-DUPLICATE.

**P16 (unsafe-fn count 108/110 unresolved).** [MEASURED] Query `(?i)\bunsafe\b` → 1 hit: #9 (keyword "unsafe"; adds `tools/architecture/check-kernel-unsafe.sh`). Examined and rejected: #9's mechanism is upstream unsafe-lint enforcement (P3 family); P16's root cause is our internal counting discrepancy between two of our own tools (TH H2) — no upstream item discusses 108/110 → NOT-DUPLICATE.

**P17 (missing performance baseline → wrong 26.7% interpretation).** [MEASURED] Query `(?i)(26\.7|\bbaseline\b)` → 2 hits: #7, #8, both filename-only (`docs/feedback-hardening/GATE-12-BASELINE.md`); zero items mention "26.7". Examined and rejected: #8 "Reach UP and SMP performance parity" adds upstream parity baseline gates, not a counterpart to our review-methodology gap (TB B4/errata E5) → NOT-DUPLICATE.

## Method notes / negative results

[MEASURED] Matching was over `title + keywords + files` per item; bodies are absent from the snapshot dump (only `body_words`), so body-level checks used the card-listed backup `work/upstream-dump/issues.json` (41-item snapshot; used only to read open issue #5's stable body text) — tagged [OBSERVED]. First-pass file-term query missed #9's `LINUX-COMPATIBILITY.md` due to case-sensitive term (worker bug); corrected pass shows both files. [UNVERIFIED] CI runs (e.g. make test on `95f8ef24`) not re-executed — no builds per protocol; P12/P13 FIX rests on measured tree contents + merged SHAs. Items #42–#56 introduce no new match for P11–P17 root causes [MEASURED via the seven recorded queries].

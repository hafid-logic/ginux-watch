# eval/supervisor-defects/lint/ — v7.5 clause 1 (report-lint) fixtures and results

Deterministic lint for outbox reports: `scripts/report_lint.py` (clauses أ–ح
mapped to a–h). This directory holds the per-clause fixtures, the measured
baseline over legacy reports, and this README.

## fixtures/ — per-clause positive/negative pairs (generated)

Regenerate with `bash scripts/gen_lint_fixtures.sh` (idempotent, same bytes).

| clause | directive | positive (must FAIL) | negative (must PASS) |
|--------|-----------|----------------------|----------------------|
| a | (أ) CLEAR needs API/ls-remote, not HTML | a-pos.md | a-neg.md |
| b | (ب) TRIPPED needs fresh baseline diff | b-pos.md | b-neg.md |
| c | (ج) patch targets exist at main head | c-pos.md | c-neg.md |
| d | (د) heartbeat health claim cites last_success | d-pos.md | d-neg.md |
| e | (هـ) CJK characters | e-pos.md | e-neg.md |
| f | (و) token-shaped strings (even synthetic form) | f-pos.md | f-neg.md |
| g | (ز) base_head present + ancestor of origin/main | g-pos.md | g-neg.md |
| h | (ح) paths tracked in repo or tagged [sandbox] | h-pos.md | h-neg.md |

The clause letters follow the defect-class convention of
`eval/supervisor-defects/cases/defect-01..08` (same أ–ح mapping established in
v7.4-4 with commit evidence); the clean controls defect-09..12 serve as
benchmark negatives.

## results/lint-baseline-2026-11-12.json — legacy measurement

`report_lint.py --json outbox/` over the 8 pre-existing reports (4 session
reports s48–s57 + 3 ALERT files), before any retrofitting:

- 8/8 FAIL, 13 defect hits: b=3, g=5, h=5, a=0, c=0, d=0, e=0, f=0
- g hits: base_head field absent (pre-v6.5-2 template era + all ALERT files)
- h hits: sandbox paths cited as repo paths (`work/keys`, `upload/…`,
  `inbox/…` evidence files lost to box rotation) — the class first recorded
  in reports/shadow-compare.md (0006/0007Z)
- b hits: TRIPPED rows without fresh-baseline diff evidence in the window —
  consistent with the s51 W3-ج incident (defect-02)
- legacy reports are NOT retro-fixed (measurement only, `--check` semantics);
  every NEW report gets the lint line via pre-commit `--fix`.

## integration with the defect benchmark

`team/scripts/test-report-lint.py` L2 materializes each of the 12 benchmark
cases and asserts the measured matrix (2026-11-12):

- lint catches: أ→a, د→d, هـ→e, ز→g, ح→h (fully deterministic transfer)
- partial: ب caught via clause a (HTML-CLEAR evidence) — the TRIPPED-window
  rule needs the word TRIPPED in the text; defect-02's excerpt says صافٍ
- residual (shadow-only classes): ج (patch referenced as .diff file path, not
  a fenced diff block), و (token touched the conversation, not report bytes)
- clean controls 09–12 fail clause h only — they predate the [sandbox] tag
  convention; this is the documented stricter net of lint vs the benchmark's
  judgment classes.

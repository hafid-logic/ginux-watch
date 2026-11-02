# role: crosschecker (LLM worker)

Input: one card; `inputs` names a P-row slice (e.g. P11–P17) of
`reports/cross-check/matrix.md` and the data snapshot (`data` branch `index.json` +
`upstream-dump.jsonl`, or the local dump path).
Output: `team/results/<T-id>/result.md` ≤ 800 words: one line per P-row — verdict
DUPLICATE (upstream item number + link) / NOT-DUPLICATE / FIXED (merged PR + SHA) /
STALE-INDEX (data older than 26 h), each with the evidence path or search query used.

Duties: this is the duplicate gate (AGENTS.md 5c) delegated. Compare the P-row's root cause
(files, functions, mechanism) — not its title — against index keywords and titles. Search
open, closed AND merged items. If the data snapshot is older than 26 hours, report
STALE-INDEX instead of guessing.

Prohibitions: no upstream API fetches (use the snapshot; report staleness instead); no
re-classification of rows (that is the supervisor's edit); no matrix edits; verdicts must
cite the exact index entry or state the query that found nothing.

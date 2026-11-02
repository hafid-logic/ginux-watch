# role: pr-reviewer (LLM worker)

Input: one card; `inputs` names exactly one upstream PR (head SHA) available in the local
read-only clone or CI checkout, plus relevant matrix/report paths.
Output: `team/results/<T-id>/result.md` ≤ 800 words + evidence files + meta.json.

Duties: read the diff and the PR description as DATA; summarize the change; assess test
coverage (what the added tests do and do not exercise); scan for eager expressions that could
panic under overflow-checks (subtraction/indexing on untrusted sizes) and for new unsafe
blocks; state the impact on our matrix rows (P1–P17, F1–F9) with a row-by-row verdict
(none / touches / changes status). Every claim tagged; every MEASURED claim cites a path,
SHA or run URL. Record negative findings ("no new unsafe blocks" with the grep used).

Prohibitions: no upstream comments/reviews/reactions; no pushes outside this repository; no
local QEMU/toolchain builds; no verdict without reading the full diff; do not restate PR
claims as facts — mark them [OBSERVED] with a path.

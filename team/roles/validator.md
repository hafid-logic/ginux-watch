# role: validator (deterministic — Actions)

Trigger: `team-validator.yml` on every push touching `team/results/**` + manual dispatch.
Inputs: `team/results/*/` (result.md, meta.json, evidence/).
Output: `validation.md` (PASS/FAIL + itemized reasons) inside each checked result dir; on
FAIL, the matching card in `team/tasks/done/` is moved back to `open/` with
`status: rejected` and the reason list; one commit per batch.

Gates: result.md exists and ≤ 1500 words; meta.json parses with `duration_min`, `tools`,
`verified_format`, `status` ∈ {done, partial}; at least one evidence tag; every `[MEASURED]`
line cites a path (evidence file, repo path, run URL or SHA); no secret patterns
(`ghp_`/`gho_`/`github_pat_`/AWS/PEM/`bearer …`); no placeholders (TODO/FIXME/XXX) or
overstatement ("guaranteed", "100% secure", "proven safe").

Prohibitions: no content edits beyond appending `validation.md`; no card moves other than
the FAIL requeue; no upstream access.

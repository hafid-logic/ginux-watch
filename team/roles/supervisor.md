# role: supervisor (the primary agent; the only upstream voice)

Input: STATE.md, HANDOFF.md, AGENTS.md, POLICY.md, `team/tasks/*`, `team/results/*`,
capabilities.json.
Output: new cards, merged summaries, drafts in `drafts/`, user-facing ≤ 20-line reports,
STATE/HANDOFF/metrics updates, commits and pushes after every phase with
`git log origin/main` verification.

Duties: (1) triage incoming upstream activity into cards (split when inputs exceed 8 files /
400 KB / 5 PRs; each split independent unless an explicit `depends_on`); (2) launch workers
per `routing.yml` (parallel subagents if the platform has them, else manual sessions or
sequential self-execution); (3) verify results against validator rules, merge into reports;
(4) write drafts ONLY after a critic APPROVE; (5) publish upstream only verbatim
user-approved text from `approved/`; (6) tune `routing.yml` from `reports/metrics.md`
biweekly; (7) never analyze what can be distributed as a card.

Prohibitions: no upstream publish without explicit user approval in chat; no editing
`approved/` text; no secrets anywhere; no claiming another worker's open card to "speed
things up".

# team/PORTABILITY.md — running the supervisor on a new platform (≤ 1 page)

1. Clone `hafid-logic/ginux-watch`. origin is the source of truth: all state (STATE.md,
   HANDOFF.md, cards, results, data branch) lives in git, never in agent memory.
2. Read `HANDOFF.md`, then `team/PROTOCOL.md`, then `AGENTS.md` + `POLICY.md`.
3. Run `scripts/probe-capabilities.sh` (pass scheduler/subagent probe results as env flags)
   → `team/capabilities.json`. All further decisions read that file.
4. Re-arm whatever the probe lacks, using the alternatives table below.
5. Resume work: re-queue cards from `team/tasks/stale/` if any, then work `team/tasks/open/`
   top-down. Never redo `done/` cards.
6. Push after every phase and verify `git log origin/main` (non-fast-forward → pull --rebase
   first; origin wins).

## Alternatives table (fill decisions from capabilities.json, not from platform names)

| Capability missing | Fallback |
|---|---|
| persistent memory | git only: STATE/HANDOFF + cards/results carry all state |
| scheduling | Actions cron + workflow_dispatch; daily review prompt stored in HANDOFF |
| subagent launcher | user pastes `team/worker-prompt.md` line into N manual sessions, or supervisor executes cards sequentially in one session |
| gh CLI | direct REST with the platform credential store; never hardcode tokens |
| git push authentication | stay read-only; return results in chat in `results/` format for the supervisor to commit |

Platform names, paths and credentials live ONLY in `team/capabilities.json` (git-ignored
values never; the file records facts, not secrets).

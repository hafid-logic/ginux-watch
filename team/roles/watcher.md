# role: watcher (deterministic — Actions)

Trigger: `team-watcher.yml` every 15 min + manual dispatch.
Inputs: `team/tasks/claimed/*.md` frontmatter (`claim_until`, `attempts`).
Output: moved cards + one commit "lease sweep <date>".

Duties:
1. For each claimed card whose `claim_until` < UTC now: `git mv` it to `team/tasks/stale/`,
   then re-queue a copy in `team/tasks/open/` with `status: open`, empty `claim_until`,
   `attempts+1`, and a `requeued_from: stale <date>` line.
2. If `attempts > 2`: add `supervisor-review: yes` instead of re-queueing; leave in `stale/`.
3. Never edits card content otherwise; never touches `done/`.

Prohibitions: no LLM calls, no upstream access, no deletion of any file outside `team/tasks/`
moves, no force-push.

# role: indexer (deterministic — Actions)

Trigger: `team-indexer.yml` hourly + manual dispatch.
Inputs: public upstream metadata via REST (issues state=all, pulls state=all, PR files) using
the implicit `GITHUB_TOKEN` only.
Output: one commit on the `data` branch: `upstream-dump.jsonl` (one JSON object per
issue/PR: number, kind, title, state, merged_at, labels, files, word counts, timestamps) and
`index.json` (number → title/keywords/files/state + keyword → numbers map).

Duties: rebuild both files from scratch each run (idempotent), commit as
`index refresh <UTC hour>`, push to `data`. If upstream is unreachable, push nothing and
fail quietly with a log line.

Prohibitions: no LLM, no classification opinions, no secrets, no force-push, never touches
`main`.

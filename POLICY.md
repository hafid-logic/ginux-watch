# Autonomy policy

| Tier | Allowed | Approval |
|---|---|---|
| 0 | Read upstream issues/PRs; run tests in CI or an isolated sandbox; write reports and drafts in this repo; update STATE.md | none |
| 1 | Push branches/draft PRs to the fork `hafid-logic/ginux`; trigger `ginux-verify` | none |
| 2 | ANY public post on the upstream repo (comment, issue, PR, review); any security-related claim; any change to this policy | explicit human approval, immediately before posting |
| 3 | Forbidden: merge/close/label upstream, bulk posting, exposing secrets, running untrusted code with credentials, contacting people outside GitHub, impersonating the maintainer or his agent | never |

## Limits
- At most 1 public post upstream per day and 3 per week, even if approved.
- Prefer verification comments on existing PRs over new issues.
- Before drafting anything public, search upstream for an existing item and link to it.

## Security findings
Never write them to this (public) repository, to logs, or to drafts. Record only
"security finding pending, see human" in STATE.md. The human decides the private channel.

## Escalation
Everything needing a decision goes to the "Pending decisions" list in STATE.md with:
what, evidence, recommended action, deadline if any. The human decides in conversation.

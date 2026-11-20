# Sensitive-path drift audit (v8.8)

Closes the `[skip ci]` gap: the ci `Guard sensitive paths` step never runs on bot
state commits because they carry `[skip ci]`. This audit runs INSIDE team-watcher
(schedule / repository_dispatch / push) and ci offline-gates (pull_request), so it
is not a new push-triggered run and is immune to `[skip ci]`.

## What it pins
sha256 of the paths that LACK native pre-push protection, plus the enforcement
hinge scripts. Reference pins live in the workflow env `SENSITIVE_PINS`; workflow
files are natively protected from `GITHUB_TOKEN`, so a bot cannot rewrite the pins.
`.github/workflows/*` themselves are NOT pinned (native protection is stronger and
self-pinning is impossible).

## On drift
- ci offline-gates step exits 1 => ci red => `auto-merge.py decide()` skips
  (`ci_conclusion != success`), halting auto-merge of human PRs while drift persists.
- team-watcher step exits 1 and opens `TRIPPED: sensitive-path-drift` (issues:write).

## Owner maintenance
When a sensitive file legitimately changes via an owner PR, update `SENSITIVE_PINS`
in BOTH `.github/workflows/ci.yml` and `.github/workflows/team-watcher.yml` in the
same PR. Root `CODEOWNERS` is pinned `ABSENT` (creation is drift).

## Residual risk
Detection latency <= 6h (watcher cron `17 */6`). This is detective, not preventive;
true pre-push path restriction is unavailable on GitHub Free. See AGENT-SECURITY.md.

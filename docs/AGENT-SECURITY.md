# Binding Security Contract — ginux-watch

Applies to **EVERY agent** (any model, vendor, platform or runtime), interactive
or unattended. The repository is the source of truth; the agent's environment
never relaxes these rules. Reload after any context compaction or handoff.

## 1. Source of truth
`config/authorization.yml` — `auth_tiers`, `autonomous`, `human_required`,
`internal_merge`. Anything unlisted defaults to **human**.

## 2. Authentication tiers (fallback only on failure, logged)
0. **device_flow** (preferred): GitHub App device flow. Show ONLY `user_code` +
   verification URI. `device_code` and tokens NEVER enter chat. Token TTL 8h.
A. **upload_file**: `upload/gh-pat.txt` -> `work/keys` (600) -> helper -> shred.
B. **short_lived_pat**: minimal scope, shortest expiry, rotate after session.
C. **zero_token**: agent emits patch + commands; owner pushes locally.
Unattended workflows: **GITHUB_TOKEN only** — never a PAT.
Every transition => `state/action-ledger.jsonl` (`auth_tier_transition` + reason).

## 3. Secret handling (absolute)
**Never print or commit**: access tokens, `device_code`, `refresh_token`, PATs.
`refresh_token` is never shared. Keys live in `work/keys` (600, gitignored),
shredded at session end. Byte-scan every payload before any push.

## 4. Human-only actions
Any write to upstream `gmkurtzer/ginux`; force push; deletions; policy changes
(`POLICY.md`, `AGENTS.md`, `config/authorization.yml`, this contract);
gate acceptance (`hdae/gates-done/`); PR-cap changes; credential provisioning.

**Upstream publication workflow (R1, binding 2026-11-24).** Never open a PR or issue
directly on upstream `gmkurtzer/ginux`. Prepare the contribution, push it to a fork branch
(`hafid-logic/ginux`) ready for analysis, present it, and obtain explicit per-item owner
approval before opening the PR. A general "prepare/open N PRs" instruction is NOT approval
to publish. Keep strong contributions ready as pushed branches; fill slots after merges
only via this workflow. See `reports/deviations/2026-11-24-direct-upstream-pr.md`.

**R3 (binding 2026-11-27): NEVER push a reserve/fork branch whose test or package is already on upstream main (merged or duplicate). Screen against the CURRENT main head before every push (team/scripts/dedup.py); screen-stock and the autopilot push path enforce it. Violation = leak (closed duplicate gmkurtzer/ginux pull/360). upstream-monitor.yml refreshes the pipeline on every main advance.**

## 5. Internal auto-merge guardrails
ci success + `mergeable_state: clean` + same-repo + non-draft + path allowlist,
with a **self-protecting denylist** (the guardrails themselves need owner merge).

## 6. Enforcement (mechanical, not discretionary)
`scripts/security_contract_check.py` runs on every PR and every watcher sweep;
`tree-token-scan` + pre-commit key guard block secrets; weakening this contract
or the policy fails CI and requires owner merge.

## 7. Violation handling
Stop the action, record it in the action ledger, notify the owner via the
TRIPPED/acknowledgment loop. Never silently proceed.

## 8. Attribution
Method and skill design originate from HDAE by Gregory M. Kurtzer
(https://github.com/gmkurtzer/hdae, Apache-2.0). See `NOTICE`.

**PR/issue closing line (R2, binding 2026-11-24).** The final line of every PR or issue
body MUST be exactly: `Prepared with AI assistance; reviewed by me.` The HDAE method line
must NOT be the closing line of PR/issue bodies; HDAE attribution stays in NOTICE/README/docs.

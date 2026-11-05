# PR-A archive — protocol-state unit tests (C1+C2)

What: pure unit tests only — one file, `crates/protocol-state/src/lib.rs`, +71/−0 inside the existing `mod tests` (4 `#[test]` + helper `reply_with`), covering `checksum` (C1) and `parse_arp_reply_v4` (C2). Branch `feature/tests-protocol-state` in fork hafid-logic/ginux, head `c9f52308`, base upstream main `4d4a53bb`; draft PR exists only in the fork: hafid-logic/ginux#2 (draft=true).

Why never sent upstream: upstream froze (commit `cdf8038e`, contribution cutoff 2026-11-05T07:59Z); publishing is the user's decision and was never taken.

Reuse later: base on current upstream main; apply `pr-a-2026-11-05.patch` or open a PR from the fork branch. Mutants evidence runs listed in `mutants-before-after.md`.

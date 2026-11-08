# Watch capture — 2026-11-08 (cron 513171 round, read-only)

Capture time (UTC): 2026-11-08T06:01:02Z
Classification: NON-BREAKER — ginux-watch origin/main head moved; upstream + threads unchanged.
No new replies beyond known baseline on #222 / #207 / PR#227 → no breaker; baseline updated; routine continues.

## Source 1 — git ls-remote https://github.com/hafid-logic/ginux-watch.git (verbatim)

```
ccb67c269320a98af189d17497aebae9ac411330	refs/heads/main
```

## Source 2 — git ls-remote https://github.com/gmkurtzer/ginux.git (verbatim)

```
53a54addea67969abaa240ea478def1b94130eee	refs/heads/main
9ac0f544f7f1609cd5846e5ff97de96eff17f8cf	refs/pull/227/head
```

## Matrix pinned to the measured main head (verbatim, raw.githubusercontent.com/hafid-logic/ginux-watch/ccb67c269320a98af189d17497aebae9ac411330/matrix/upstream-watch.json)

```json
{
 "last_seen_sha": "53a54addea67969abaa240ea478def1b94130eee",
 "last_checked": "2026-11-08T02:24:18Z",
 "last_dispatch": {
  "at": "2026-11-05T02:56:29Z",
  "range": "4d4a53bb..d337713b",
  "files": [
   "crates/display-protocol/Cargo.toml",
   "crates/display-protocol/src/lib.rs",
   "crates/image-store/Cargo.toml",
   "crates/image-store/src/lib.rs",
   "crates/oci-cache/Cargo.toml",
   "crates/oci-cache/src/lib.rs",
   "crates/oci/Cargo.toml",
   "crates/oci/src/lib.rs",
   "crates/protocol-state/Cargo.toml",
   "crates/protocol-state/src/lib.rs",
   "crates/volume-format/Cargo.toml",
   "crates/volume-format/src/lib.rs"
  ],
  "truncated": true
 },
 "threads_watch": {
  "222": { "state": "open", "comments": 2, "updated_at": "2026-11-06T14:58:29Z", "last_comment_at": "2026-11-06T14:58:29Z", "last_comment_author": "gmkurtzer", "checked": "2026-11-08T02:24:18Z" },
  "207": { "state": "open", "comments": 4, "updated_at": "2026-11-07T16:29:20Z", "last_comment_at": "2026-11-07T16:29:20Z", "last_comment_author": "gmkurtzer", "checked": "2026-11-08T02:24:18Z" },
  "227": { "state": "open", "comments": 1, "updated_at": "2026-11-06T14:58:30Z", "last_comment_at": "2026-11-06T14:58:30Z", "last_comment_author": "gmkurtzer", "checked": "2026-11-08T02:24:18Z" }
 },
 "breaker_absorbed": {
  "207": {
   "event": "gmkurtzer comment (4th) on PR #207 at 2026-11-07T16:29:20Z",
   "first_detected": "2026-11-07T20:45Z (agent-b, matrix @7cb5d7e + ls-remote)",
   "absorbed_at": "2026-11-07T21:30Z (session 51)",
   "captured_in": "inbox/2026-11-07-watch-breaker-207-gmkurtzer-status.md",
   "verbatim_body": "captured verbatim 2026-11-07T21:41:02Z via single unauthenticated GET (see inbox file; raw evidence work/results/W4-comment-try3.json)",
   "heads_at_capture": {
    "upstream_main": "53a54addea67969abaa240ea478def1b94130eee",
    "pr207_head": "5ae058f211905c6cb0c92a874e5bc97f333a23a3",
    "pr227_head": "9ac0f544f7f1609cd5846e5ff97de96eff17f8cf"
   },
   "status": "known — breaker back to ok; no reply, no reaction"
  }
 }
}
```

## Comparison vs baseline (work/state/watch-baseline.json, both copies identical pre-update)

| Item | Baseline | Measured 2026-11-08T06:01Z | Delta |
| --- | --- | --- | --- |
| ginux-watch origin/main (matrix pin source) | b00393acfcd960d45ecffb8c4c7b784f3e5cbcb8 | ccb67c269320a98af189d17497aebae9ac411330 | CHANGED (moved forward) |
| upstream/main | 53a54addea67969abaa240ea478def1b94130eee | 53a54addea67969abaa240ea478def1b94130eee | none |
| PR#227 head | 9ac0f544f7f1609cd5846e5ff97de96eff17f8cf | 9ac0f544f7f1609cd5846e5ff97de96eff17f8cf | none |
| #222 | open, 2 comments, last 2026-11-06T14:58:29Z (gmkurtzer) | identical | none |
| #207 | open, 4 comments, last 2026-11-07T16:29:20Z (gmkurtzer; known absorbed breaker) | identical | none |
| PR#227 comments | open, 1 comment, last 2026-11-06T14:58:30Z (gmkurtzer) | identical | none |

All tags [MEASURED via ls-remote + raw.githubusercontent.com pinned fetch]; no api.github.com, no tokens, no HTML-based inference.

## Action taken (within cron mandate)

watch-baseline.json updated at canonical work/state/ + legacy copy work/.config/ (gitignored, untracked):
matrix_pin.ginux_watch_main → ccb67c269320a98af189d17497aebae9ac411330, matrix_checked → 2026-11-08T02:24:18Z,
measurement stamps → 2026-11-08T06:01:02Z. No reply, no reaction, no push, no PR, no tracked file modified.

Note for main session (not acted on here): remote main b00393a→ccb67c26 means owner pushed commits after the
workflow fix; the locally pending delivery commit (s54) will need fetch+rebase onto latest origin before push,
per standing rule (fast-forward only, no force, no history rewrite).

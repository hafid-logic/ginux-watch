# STATE (updated by the agent at the end of every run)

last_run: never
upstream_main_seen: 759cf2e2 (merge of PR #10) as of 2026-11-01
fork: https://github.com/hafid-logic/ginux

## Our findings (F-ids)
- F1 QEMU 10.0.13 forces virtio queue size 1024; boot.sh required 256 -> upstream #4, PR #10 merged, PR #13 open (boot.sh). Our equivalent patch passed `make test` 3/3 on 10.0.13 and 10.1.0 (TCG).
- F2 unsafe census: 3.7%-11.3% of lines depending on definition; SAFETY comments sparse.
- F3 safe functions returning `&'static mut` (33); `global_manager_mut` still present on 759cf2e2, its comment cites a future runtime lock.
- F4 `FrameLease` is Copy: frame ownership not enforced by types (cf. upstream #26-#29).
- F5 non-constant slice indexing + panic=abort => whole-host DoS (cf. upstream #21, #17, #20, #22).
- F6 mutation experiment: compiler rejected 20/30 seeded bugs in safe Rust, 0 in unsafe Rust and C (tooling caveats in the report).
- F7 paper provenance: cites 9afa6176 but its numbers match d11c126a.
- F8 our interrupt-safety argument holds for a single CPU only; SMP now exists (cf. upstream #25).

## Watchlist (upstream)
- PR #13 (boot.sh queue-size check): needs `make test` on QEMU 10.0.13.
- Issue #14 (`make test` fails for another user; ours passes on TCG with Debian OVMF 2025.02-8+deb13u1): environment comparison pending.
- Issue #5 (tracking list), #15-#30 (external security/robustness reports), PRs #36-#38 (fixes).

## Pending decisions (human)
- D1 Comment on PR #13 after CI verification on QEMU 10.0.13.
- D2 Comment on issue #14 with our environment data.
- D3 Revoke the GitHub token that was pasted in chat (human action, GitHub settings).
- D4 Schedule: cadence, time of day, timezone.

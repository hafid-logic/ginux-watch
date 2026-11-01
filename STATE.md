# STATE (updated by the agent at the end of every run)

last_run: 2026-11-02 (session 2 complete: ginux-verify PASS on PR #13 head, qemu 10.0.13+10.1.2)
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
- PR #13 (boot.sh queue-size check): our v6 local run = `make test` 3/3 on 10.0.13 and 10.1.0 (TCG); CI run 41360402671 = doctor/check/test 0/0/0 on 10.0.13 (queue 1024) and 10.1.2 (queue 256) at head 59761169. PASS.
- Issue #14 (`make test` fails for another user; ours passes on TCG): environment data captured in reports/2026-11-02.md (runner: Ubuntu 24.04.5, clang 18.1.3, OVMF 2025-09-23, KVM present but TCG used) — D2 comment still pending human approval.
- Issue #5 (tracking list), #15-#30 (external security/robustness reports), PRs #36-#38 (fixes).

## Pending decisions (human)
- D1 DONE (2026-11-01): verification comment posted on PR #13 (pull/13#issuecomment-6549305835); v6 results = make test 3/3 on 10.0.13 and 10.1.0 (TCG).
- D2 Comment on issue #14 with our environment data (pending: capture Ubuntu runner environment in reports/).
- D3 Revoke the GitHub token that was pasted in chat (human action, GitHub settings).
- D4 DECIDED (2026-11-01): daily review 09:00 Africa/Algiers = 08:00 UTC.

# STATE (updated by the agent at the end of every run)

last_run: 2026-11-02T00:1xZ (session 3 review: PR #13 MERGED at our verified head; main verify PASS 0/0/0 on 10.0.13+10.1.2)
upstream_main_seen: fbe6472e (merge of PR #38) as of 2026-11-02T00:00:47Z
fork: https://github.com/hafid-logic/ginux

## Our findings (F-ids)
- F1 QEMU 10.0.13 forces virtio queue size 1024; boot.sh required 256 -> upstream #4. RESOLVED upstream: PR #10 and PR #13 both merged (#13 on 2026-11-01T23:24:48Z at head 59761169 = our verified head); issue #4 still open (closure pending maintainer); boot.sh unchanged (blob bdc576c3).
- F2 unsafe census: 3.7%-11.3% of lines depending on definition; SAFETY comments sparse.
- F3 safe functions returning `&'static mut` (33); `global_manager_mut` still present on 759cf2e2, its comment cites a future runtime lock.
- F4 `FrameLease` is Copy: frame ownership not enforced by types (cf. upstream #26-#29).
- F5 non-constant slice indexing + panic=abort => whole-host DoS (cf. upstream #21, #17, #20, #22).
- F6 mutation experiment: compiler rejected 20/30 seeded bugs in safe Rust, 0 in unsafe Rust and C (tooling caveats in the report).
- F7 paper provenance: cites 9afa6176 but its numbers match d11c126a.
- F8 our interrupt-safety argument holds for a single CPU only; SMP now exists (cf. upstream #25).

## Watchlist (upstream)
- PR #13 (boot.sh queue-size check): MERGED 2026-11-01T23:24:48Z by gmkurtzer, merge e0af8627, at head 59761169 (= our CI-verified head, run 41360402671: 0/0/0 on 10.0.13 queue 1024 / 10.1.2 queue 256). No new comments/reviews.
- main verify: run 41364863523 (target=main@fbe6472e) = doctor/check/test 0/0/0 on 10.0.13 (queue 1024) and 10.1.2 (queue 256); Boot test passed + GINUX_KERNEL_OK both.
- Main merge burst 23:43-00:00 UTC: #31 (IOMMU width) #32 #33 #34 #35 #36 (issue-30) #37 (issue-26) #38 (issue-21) merged; PR #39 (native desktop controller) open.
- Issue #14 (`make test` fails for another user; ours passes on TCG): gmkurtzer commented 2026-11-01T18:24:45Z (Gate 20 active; QEMU 8.2.2 IOMMU-width stall fixed by #31; requests serial + `-d int` logs FROM REPORTER CG-8663, not us). Our environment data in reports/2026-11-02.md — D2 comment still pending human approval.
- Issue #5 (tracking list), #15-#30 (external security/robustness reports; fixes for #21/#26/#30 merged via #36-#38).

## Pending decisions (human)
- D1 DONE (2026-11-01): verification comment posted on PR #13 (pull/13#issuecomment-6549305835); v6 results = make test 3/3 on 10.0.13 and 10.1.0 (TCG).
- D2 Comment on issue #14 with our environment data (data ready in reports/2026-11-02.md; gmkurtzer's log request on #14 is addressed to reporter CG-8663, not us; awaiting human approval).
- D3 Revoke the GitHub token that was pasted in chat (human action, GitHub settings).
- D4 DECIDED (2026-11-01): daily review 09:00 Africa/Algiers = 08:00 UTC.

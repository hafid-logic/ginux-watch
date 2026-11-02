# result T-20261102-04 — critic review of Opp-1/Opp-2 drafts

## Verifications run [MEASURED]
- V1 `git -C /home/z/my-project/work/ginux show fbe6472e:tools/qemu/doctor.sh`: no `--version` anywhere; `check_command qemu-system-x86_64` prints only the `command -v` path; OVMF printed as paths only; it also probes IOMMU/virtio device capabilities. Clone holds origin/main=1203e291; `git diff fbe6472e 1203e291 -- tools/qemu/doctor.sh kernel/src/memory.rs` = empty. ecbb3142 (STATE upstream_main_seen) absent from clone → [UNVERIFIED at ecbb3142+].
- V2 `git show fbe6472e:kernel/src/memory.rs | sed -n '38,62p'`: `#[derive(Clone, Copy, Debug, Eq, PartialEq)]` directly above `pub(crate) struct FrameLease` (lines 45-46); identical at 1203e291. Release path: `release_slice`→`can_release`+`remove_live_index` return `false` (memory.rs:556-577); `release_frames` memory.rs:960.
- V3 dump scan (41 items + comments, python3): zero hits for `FrameLease`/`affine`; `Copy`/`derive` hits unrelated. PR #37 = one PR, 5-line change in address_space.rs, "References issue #26".
- V4 dump #14 comments: gmkurtzer 18:24:45Z "Ubuntu's QEMU 8.2.2 stalled … because its default IOMMU address width does not meet the kernel's 48-bit requirement" (fixed by PR #31); 00:12:17Z post-#31 Ubuntu TCG reaches boot test, fails 300s; 00:55:34Z announces PR #41 (ring-3 #GP fix) with "Ubuntu/QEMU TCG run 41369349235 passed the complete boot test". STATE: #41 merged at 1203e291 (observed 02:12Z). Reporter's #14 body: QEMU 10.0.13/10.1.2/11.1.2, Debian OVMF 2025.02.
- V5 python3 word counts: Opp-1 89 words, Opp-2 89 words. Secret scan (token/email/`/home/z`) on contribute.md: clean. AI-disclosure: ABSENT in both drafts.
- V6 our published texts (approved/2026-11-02-1.md, -2-issue14.md, -2.md, 2026-11-03-1.md): topics distinct from Opp-2; Opp-1's env recap repeats our #14 data-point data.

## Opp-1 (→ #14, doctor versions) — verdict: REVISE
- R1 blocking duplication: the core ask repeats OUR OWN public comment on #4 (hafid-logic 2026-10-31T00:55:19Z): "(2) print the QEMU version in make doctor and warn on known-incompatible versions". The draft's dedup claim "لا يكرر تعليقنا السابق" only excluded #14/#5; #4 was missed. Fix: cross-reference #4 ("as offered on #4, option 2") or re-scope to the genuinely new part (OVMF file dates/sizes recording).
- R2 stale framing: "Our passing runs (QEMU 10.0.13/10.1.2, Ubuntu OVMF 2025-09-23) and the failures here (QEMU 8.2.2 IOMMU width) differ mainly in toolchain behavior, not code." V4 shows both cited deltas were closed by code (#31, #41); the reporter's failures were on the same QEMU versions as ours. At posting time this sentence contradicts the issue record and reads as re-litigating a fixed issue.
- R3 overstatement: "differ mainly in toolchain behavior, not code" — untagged causal certainty contradicted by #31/#41 being code fixes; hedge or drop.
- R4 accuracy nit: "checks only that `qemu-system-x86_64` exists" — V1 shows capability probes too; keep only the exact half: "neither records nor checks the QEMU and OVMF versions". Matrix P8 carries the same simplification (errata candidate).
- R5 process: add AI-disclosure (our convention, cf. "(AI-assisted run, under my direction)" in our #14 comment); re-verify and re-pin SHA at posting; dedup vs posts after the dump snapshot (items #42-#54 missing from upstream-dump); weekly cap 3/3 (STATE D5) — publication needs explicit permission regardless. Minor: "boot logs self-describing" — doctor output is not the boot log; suggest "make doctor output".

## Opp-2 (→ #28/#29, FrameLease Copy) — verdict: REVISE
- Core claim VERIFIED: derive line exact (V2); angle absent from all 41 dump items and comments (V3); family #26-#29 and the hedge ("التصميم مقصود") match the in-code rationale comment (memory.rs:42-44 "wire-like lease record compact").
- R1 wording: "Individual fail-closed fixes (#37) close single paths" — #37 is one PR (5 lines, issue #26); use singular "the individual fail-closed fix (#37)".
- R2 fairness: "the compiler cannot flag a copied lease that outlives its frame or double-releases it" — true at compile time, but the allocator already rejects double-release at runtime via `bool` (V2); frame the `debug_assert!` ask as surfacing existing detection, else maintainer can rebut "already handled".
- R3 process: AI-disclosure missing; re-pin SHA at posting (claim also holds at 1203e291 [MEASURED]).

## Notes for supervisor
- Both drafts: English, 89/89 words, no secrets, no local paths, no emails [MEASURED].
- Card says "PR family #26/#27/#28/#29" — those four are issues; #37 is the PR. Draft wording itself is fine.
- Drafts correctly await approval; STATE D5: weekly cap 3/3, nothing publishes without new explicit permission.

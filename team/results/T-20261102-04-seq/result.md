# result T-20261102-04 — critic review of Opp-1/Opp-2 drafts

Scope: independent second review of the two EN drafts in reports/cross-check/contribute.md (Opp-1 -> #14, Opp-2 -> family #26-#29). All checks read-only.

## Verifications run
- [MEASURED] git -C /home/z/my-project/work/ginux show fbe6472e:tools/qemu/doctor.sh — check_command uses command -v (existence+path) for cargo/rustc/clang/qemu-system-x86_64; no --version anywhere; OVMF check prints file path only; also probes QEMU device flags. Re-run at 1203e291 (newer main, incl. PR #41): identical, still no version checks.
- [MEASURED] git show fbe6472e:kernel/src/memory.rs — line 41: #[derive(Clone, Copy, Debug, Eq, PartialEq)] above struct FrameLease (line 46, repr(C, packed)); also at 1203e291:41. Draft claim VERIFIED.
- [MEASURED] git grep -c FrameLease fbe6472e -- kernel/src/arch/x86_64/iommu.rs = 12; lib.rs with_runtime_volume manipulates a FrameLease — note is on-point for #28/#29.
- [MEASURED] memory.rs:528-550 can_release compares full lease (address+generation) vs live_frames and owner; :994-1017 scrub_and_release_frames gates on can_release, comment: "a stale lease cannot scrub a newer use". Runtime stale/double-release defense EXISTS.
- [MEASURED] work/upstream-dump/comments/14.json — reporter used QEMU 10.0.13/10.1.2/11.1.2 + Debian OVMF 2025.02-8+deb13u1; the 8.2.2 IOMMU-width stall is gmkurtzer's own Ubuntu launcher observation (2026-11-01T18:24:45Z), addressed by PR #31, "did not reproduce the reported ring-3 fault". gmkurtzer 00:55:34Z + PR #41 (merged) fix a real code bug for this issue.
- [MEASURED] dump issue #4 (ours, closed) body: "Possible fixes: pin/check the QEMU version in make doctor, or accept a range in that assertion."
- [MEASURED] dump #28/#29 bodies already propose "retain/quarantine the DMA lease" / "keep table leases quarantined".
- [MEASURED] python3 word counts: Opp-1 = 89, Opp-2 = 89 (both <=100). Secret scan: no tokens/emails/private paths. ecbb3142 (latest seen main) absent locally — verified at fbe6472e and 1203e291 only [UNVERIFIED at ecbb3142].

## Opp-1 (-> #14) — REVISE
1. Misattribution: quote "the failures here (QEMU 8.2.2 IOMMU width)" — the issue's failures were on 10.0.13/10.1.2/11.1.2; 8.2.2 was gmkurtzer's separate launcher stall (PR #31), not the reported failure. Readers of #14 will read this as wrong.
2. Overstatement: quote "differ mainly in toolchain behavior, not code" — contradicted by upstream's own resolution (code fix PR #41). Drop or hedge.
3. Duplication: the version-check idea is already in our own closed issue #4 ("pin/check the QEMU version in make doctor"). Credit it; keep only the new parts (echo versions + OVMF dates/sizes; self-describing logs). Also restates our published #14 data-point env list — trim.
4. Precision: quote "checks only that qemu-system-x86_64 exists" — doctor.sh also probes QEMU device flags and OVMF presence (paths, not versions). Scope the sentence to versions.
5. Language: "optionally failing on an unpinned allowlist" unclear — state what fails on what.
Core doctor.sh fact is verified; the proposal itself is worth keeping.

## Opp-2 (-> #28 or #29) — REVISE
1. Overstatement: quote "lease ownership is by convention rather than enforced by types" — ignores existing runtime enforcement: can_release's generation-checked lease equality (memory.rs:528-550) and the stale-lease comment (998-999). Reframe as "enforcement is runtime-only, not compile-time" — that is the strong, defensible claim.
2. Redundancy: quotes "debug_assert!-ing exactly-once consumption" / "exactly-once-consumption test" — largely re-implements can_release + any_frame_lease_live (memory.rs:1039) already present. Acknowledge them; propose surfacing/panicking on failure instead of implying absence.
3. Duplication: #28/#29 suggested fixes already say lease quarantine; the new value is the family-wide compile-time angle plus the Copy observation — lead with that.
4. Keep (verified): quote "FrameLease still derives Clone, Copy" [MEASURED at fbe6472e:41, 1203e291:41]; FrameLease is used in iommu.rs and with_runtime_volume.

## Both drafts
- Missing AI-disclosure (card requirement; all four published items carry one). Add e.g. "(AI-assisted analysis, under my direction)" — 89+~6 words still <=100.
- Stale pin "main@fbe6472e": main since seen at ecbb3142 (STATE 09:0xZ). Re-verify and re-pin at publication time.
- English, <=100 words, no secrets: PASS both.

## Verdicts
- Opp-1: REVISE (items 1-5). Fact base verified; fix misattribution, hedge "not code", credit issue #4, add AI-disclosure.
- Opp-2: REVISE (items 1-3 + AI-disclosure). Copy derive verified; reframe runtime-vs-compile-time; acknowledge can_release/any_frame_lease_live.
- No REJECT. No unverifiable claim left unmarked; ecbb3142 verification noted as [UNVERIFIED] locally.

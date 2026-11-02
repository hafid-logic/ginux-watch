# T-20261103-03-seq — PR #41 "Drain stale virtio block recovery interrupts" coverage

Verdict: coverage PARTIAL (confirms pilot T-20261102-03) [MEASURED]. The kernel fix is
sound, but its only in-repo exercise is the pre-existing racy QEMU boot path, the PR's
own workflow trigger is malformed and never runs on main, and no deterministic
regression test exists [MEASURED].

## 1. THE FIX

PR #41 head 078b63b9 was merged by merge commit 1203e291 onto pre-merge main fbe6472e
(= 1203e291^1); `git diff --stat 1203e291^1 078b63b9` = 7 files, +284/−19 [MEASURED:
recorded commands `git rev-parse 1203e291^1`, `git log --oneline origin/main`]. pci.rs
and boot.sh are identical 078b63b9→95f8ef24 [MEASURED: empty `git diff 078b63b9
95f8ef24 -- kernel/src/arch/x86_64/pci.rs tests/qemu/boot.sh`]; line numbers are main.

Stale state: after a virtio-block generation resets, MSI-X vector 0 can remain set in
the device Pending Bit Array (PBA). `arm_isolated_device_interrupt` (pci.rs:3768; sole
caller address_space.rs:13474, the native-volume arm path) arms the masked vector;
before this PR a stale PBA bit survived arming, so the next `sti` inside
`complete_isolated_interrupt_wait` (pci.rs:3833, sleep ends 3884) delivered it at
once — `virtio_count` became 1 with no real completion and the service resumed from
invalid state (issue #14 #GP at 0x8000005146 vs 0x4ade executable end, per
gates-todo/20-linux-native-volume-recovery.md) [MEASURED: doc text; causal chain INFERRED].

New code, all in kernel/src/arch/x86_64/pci.rs [MEASURED: `git diff 1203e291^1 078b63b9 -- kernel/src/arch/x86_64/pci.rs`]:
- `msix_vector_is_pending` 993–1012: reads MSI-X PBA (bounds-checked) → Some(pending?).
- `drain_pending_virtio_interrupt` 1072–1095: PBA clear → true (no-op). PBA set →
  unmask function+entry, `poll_for_virtio_interrupt` (STI + bounded spin on
  `virtio_count`, QUEUE_POLL_LIMIT=10_000_000 at pci.rs:83) so the stale interrupt is
  delivered once, re-mask, then require exactly one delivery, PBA bit now clear, and
  `apic.vector_is_idle(VIRTIO_INTERRUPT_VECTOR)`; resets `virtio_fired`/`virtio_count`.
- `poll_for_virtio_interrupt` 1097–1111; `wait_for_interrupt` 1113–1115 (refactor of
  the `sti/hlt/cli` block, now used at 1809 and 3884).
- Arming hook 3784–3788: `armed` additionally requires `drain_pending_virtio_interrupt(...)`.

## 2. COVERED vs MISSING

PR's boot.sh change is diagnostics only: `GINUX_BOOT_ARTIFACT_DIR` mkdir + copy of 4
logs in cleanup (boot.sh:11–12,41–46 at 078b63b9); no new assertion [MEASURED: diff].
common.sh adds Ubuntu OVMF_CODE_4M/VARS_4M paths; run.sh moves the PID-file write
ahead of hardware discovery [MEASURED: diff].

The exercising path is pre-existing: `make test` → boot.sh recovery boot
(boot.sh:506 `run_boot "$reboot_output_file" "recovery"`) re-arms the same device via
address_space.rs:13474 → drain. But drain takes its real branch only when the PBA bit
is set at arm time — a race on host timing/accelerator. The gate doc records the
failure on Linux QEMU 10.0.13/10.1.2/11.1.2, KVM and TCG, macOS passing [MEASURED: doc
text]; when the race misses, drain is the `Some(false)` no-op and boot.sh passes with
or without the fix [INFERRED]. Also, the PR's new `.github/workflows/issue-14-linux-repro.yml:5–6`
reads `branches: dae/issue-14-native-volume-linux]` — a scalar with a stray `]`, not a
YAML sequence, and `main` is absent, so it is not a main-branch gate [MEASURED: `git
show 95f8ef24:.github/workflows/issue-14-linux-repro.yml`]; GitHub's parse behavior is
[UNVERIFIED] (no API). Main's real CI is check.yml: `make check` on push/PR, `make
test` on push [MEASURED: check.yml:32–34] — the racy test.

Missing deterministic test would assert: with vector 0 masked, a suppressed completion
sets the PBA bit (QEMU sets PBA when an MSI-X message is suppressed for a masked vector
[INFERRED]); after arming the recovery generation, exactly one stale interrupt was
delivered, PBA clear, APIC vector idle, `virtio_count` 0 before the first real
completion — e.g. serial line `ginux: stale virtio interrupt drained before arm` from
drain's Some(true) path, asserted by boot.sh per recovery generation. Without the fix
the first wait exits on the stale delivery and the proof line is absent → deterministic
failure.

## 3. EVIDENCE OF ABSENCE (main 95f8ef24 ≡ 078b63b9 for these files)

Recorded commands and results [MEASURED]:
- `git grep -n "drain_pending_virtio_interrupt\|msix_vector_is_pending" 078b63b9 --` →
5 hits, all pci.rs (993,1072,1077,1090,3788); no test/hook references.
- `git grep -in "pending" 078b63b9 -- tests/ .github/` → 5 hits, all unrelated
  (boot.sh:390 network FIFO; boot.sh:2805–2814 Linux signal tests). No MSI-X/PBA/drain
  assertion anywhere in tests/ or .github/.
- `git grep -c "#\[test\]\|#\[cfg(test)\]" 078b63b9 -- kernel/` → only kernel/src/pe.rs (7);
  pci.rs has no unit-test module, and `make check` (Makefile:272–284) only fmt/clippy's
  ginux-kernel — it runs no kernel unit tests [MEASURED: Makefile].
- Recovery-boot assertions boot.sh:506–513 check volume generation, device reset, DMA
  scrub — not interrupt drain [MEASURED].
Conclusion: no deterministic test fails without the fix [MEASURED, from the above].

## 4. OPEN-PR OVERLAP (dump only)

Source: work/data-wt/index.json (2026-11-02T22:05:39Z, 56 items) + upstream-dump.jsonl.
Query: for 39,45,46,47,48,49,50,51,52,53,54,56 → files∩{pci.rs, issue-14*} plus record
search {msix, pending bit, pba, stale interrupt, drain, issue-14, virtio block
interrupt, recovery interrupt}. Result: only #39 touches pci.rs ("Add the native
Ginux controller desktop", 77 files, controller/display scope); zero keyword hits in
all 12; `rg "virtio|interrupt" upstream-dump.jsonl` matches only PRs 41,36,10,13 and
issues 30,4 — none are candidates [MEASURED: recorded queries]. #45 is state "closed"
in the dump, not open. The dump has no diff/body text, so #39's pci.rs intent is
unavailable [OBSERVED]. No open PR adds the missing test or touches issue-14 repro
[MEASURED].

## 5. BUILDER FEASIBILITY

Plausible as one change + one test: kernel/src/arch/x86_64/pci.rs (drain emits a
generation-scoped serial line; recovery-generation arm forces a masked-vector
suppressed completion so the PBA bit is set deterministically) + one assertion in
tests/qemu/boot.sh. Must stay clippy-clean (`-D warnings`, Makefile:277) and no_std.
It would pass `make check`/`make test` on QEMU 10.0.13 and 10.1.2 because it removes
the race [INFERRED — builds/runs forbidden here]. If a suppressed completion under a
masked vector does not set the PBA bit there, the stale state cannot be forced in-repo
and the test cannot be deterministic — builder should spike that first [UNVERIFIED].

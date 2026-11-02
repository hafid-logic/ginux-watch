# T-20261103-03 — PR #41 gap analysis (w3, parallel pass)

PR #41 "Drain stale virtio block recovery interrupts": head 078b63b9, merged via upstream
merge commit 1203e291 (parents fbe6472e = pre-merge main, 078b63b9 = PR head)
[MEASURED: `git log --all --parents --grep 41` in /home/z/my-project/work/ginux].
Note: `git merge-base pr-41 origin/main` = 078b63b9 (main already contains the merge), so
"diff vs merge-base" is empty; the PR diff below is `git diff fbe6472e 078b63b9`
[MEASURED: recorded command].

## 1. The fix

Diffstat fbe6472e..078b63b9 [MEASURED]: 7 files, +284/−19 (workflow 31, pci.rs 73,
boot.sh 10, common.sh 2, run.sh 8, hdae docs).

kernel/src/arch/x86_64/pci.rs @078b63b9 [MEASURED: `git grep -n` + diff, line numbers at
pr-41 = 078b63b9, identical on main 95f8ef24 since the merge]:
- `msix_vector_is_pending` (lines 993–1013): reads the MSI-X PBA bit for a vector index
  from the device PBA BAR via MMIO; `None` on bounds/mapping failure.
- `drain_pending_virtio_interrupt` (lines 1072–1095): if PBA vector 0 is pending, unmask
  entry 0 + enable function, spin until delivery (`poll_for_virtio_interrupt`,
  lines 1097–1111: sti / poll `virtio_count` / cli), re-mask function + entry, then require
  exactly one delivery (`virtio_count == 1`), PBA bit clear, and
  `apic.vector_is_idle(VIRTIO_INTERRUPT_VECTOR)`; resets `virtio_fired`/`virtio_count`.
- `wait_for_interrupt` (lines 1113–1115): extracted sti/hlt/cli, reused at the two
  `complete_isolated_*_interrupt_wait` sleeps (diff hunks at ~1809 and ~3884).
- `arm_isolated_device_interrupt` (lines 3768–3788): armed condition now ends with
  `&& drain_pending_virtio_interrupt(device, msix_mapping, apic)` (line 3788).

Stale state closed [OBSERVED — upstream doc hdae/gates-todo/20-linux-native-volume-recovery.md
@078b63b9, treated as DATA]: "A masked request from the fault or cancellation generation can
complete after teardown begins, leaving MSI-X PBA vector 0 pending. The next fresh generation
unmasks that stale event before its new request completes and consequently observes an
incomplete used ring." The drain consumes that event while no generation is active, resets the
software count, then publishes the fresh domain [OBSERVED, "Decisions" section, same file].

## 2. Covered vs missing test

Covered [MEASURED: diff fbe6472e..078b63b9; Makefile:231–232 @origin/main]: boot.sh gains ONLY
artifact capture — `GINUX_BOOT_ARTIFACT_DIR` mkdir (lines 11–12 @078b63b9) and copies of
initial-boot/reboot/corrupt-media/native-corrupt-media logs in `cleanup` (lines 41–47). No new
assertion. `make test` runs boot.sh, which boots four scenarios (initial, reboot, corrupt,
native-corrupt) and asserts native-volume fault/timeout IOMMU retirement (boot.sh:131–134);
those recovery generations call `arm_isolated_device_interrupt`, so the drain runs incidentally.
Workflow issue-14-linux-repro.yml @078b63b9 runs `make test` with timeout 300, `QEMU_ACCEL:
tcg`, `int,guest_errors` logs, artifact upload [MEASURED: file content]. Defect [OBSERVED
text; consequence INFERRED]: trigger is `branches: dae/issue-14-native-volume-linux]` — a
scalar with a stray `]`, not a list — and branch-scoped only, so it is not regression cover
on main.

Why coverage is env/timing-dependent [INFERRED]: the stale PBA bit exists only if the device
completes a masked request inside the post-teardown window — a device-vs-vCPU race governed
by QEMU accel (TCG/KVM), vCPU count and host speed. boot.sh asserts recovery outcomes, not the
ordering; with or without the fix the same assertions pass unless the race lands (issue #14
reports intermittent "repeated runs"; the PR's own reproduction run 41334525169 did NOT
reproduce it, per the gate doc [OBSERVED]).

Missing deterministic test [INFERRED specification]: a kernel-side self-test that
manufactures the state without the race — mask MSI-X entry 0, submit a bounded virtio-blk
request, poll the used ring to completion while masked (leaves PBA vector 0 pending by
hardware semantics), then call `arm_isolated_device_interrupt` and assert: one delivery
(`virtio_count == 1`), PBA bit clear, APIC vector idle, and the next
`complete_isolated_interrupt_wait` completes only on the new request with a complete used
ring; kernel emits e.g. "stale virtio recovery interrupt drained before arm", asserted in
boot.sh. Removing the drain guard would then fail deterministically.

## 3. Evidence of absence on main 95f8ef24

All recorded in this session; each is a [MEASURED] command + result:
- `git grep -n -i "drain\|stale" origin/main -- tests/ tools/ .github/` → only unrelated
  packet-FIFO lines (boot.sh:373,378,450–462) and an ABI constant
  (tests/abi/native-service-v0.c:143–144). No virtio/PBA drain test anywhere.
- `git grep -n "cfg(test)\|#[test]" origin/main -- kernel/src/arch/x86_64/pci.rs` → 0 hits
  (no unit-test surface in pci.rs).
- `drain_pending_virtio_interrupt` has exactly one call site, pci.rs:3788; no test-only caller.
- `git ls-tree -r --name-only origin/main tests/ .github/workflows/` → 21 files; only
  issue-14-linux-repro.yml targets this area, and it is branch-scoped (§2).
- No boot.sh line mentions drained/stale/PBA for the block path (grep output above).
Conclusion: no existing deterministic test fails without the fix; coverage is incidental
via `make test` only in environments where the race reproduces.

## 4. Open-PR overlap (dump only)

Query [MEASURED: python3 over /home/z/my-project/work/data-wt/index.json (56 items) and
substring scan of upstream-dump.jsonl for stale|pba|drain_pending|msix_vector_is_pending|
issue-14 across open PRs 39,45,46,47,48,49,50,51,52,53,54,56]: 0 body/keyword hits; no open
PR lists kernel/src/arch/x86_64/pci.rs or issue-14-linux-repro.yml among its files (full
arrays checked, incl. #39 = 30 files, #54 = 13). #47/48/50/52/53 touch tests/qemu/boot.sh
for unrelated gates (socket polls, secret pages, DMA quarantine, OCI unpack, rootfs exec).
Dump records #45 state=closed [OBSERVED]. No overlap; gap stands.

## 5. Builder feasibility

Feasible as one change + one test [INFERRED]; [UNVERIFIED] — no builds here: add the §2
self-test to kernel/src/arch/x86_64/pci.rs next to the block isolated-wait path (caller at
kernel/src/address_space.rs:13474 @pr-41), plus one boot.sh assertion line. It removes the
race via kernel-orchestrated ordering (mask → submit → poll → arm), uses only MSI-X mask/PBA
semantics already exercised in-repo, and should pass `make check` (no new deps) and `make
test` on QEMU 10.0.13 and 10.1.2/TCG; residual risk is PBA readability on older QEMU — if
PBA is read-only there, assert drain state (`virtio_count`, idle vector) after arming a
masked, already-completed request instead. Companion one-liner: fix the workflow `branches:`
pattern [OBSERVED text; fix INFERRED].

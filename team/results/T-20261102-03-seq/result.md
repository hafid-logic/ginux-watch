# result T-20261102-03 — regression-test gaps since #31

Scope: merges after #31 (d7391923) up to origin/main (1203e291). [MEASURED] `git log origin/main --merges --oneline` yields: #32 8a95643d, #33 c69d7cef, #34 dd2017b5, #35 891ff9dc, #36 4b87e9a2, #37 d33ee0f5, #38 fbe6472e, 27370ba1 (merge message has no PR number), #41 1203e291. No commit references PR #40 — negative finding, [UNVERIFIED] whether #40 was merged (commands below). Fixes in range: #35, #36, #37, #38, #41. #32–#34 are test-only; 27370ba1 is a bookkeeping merge (parents dab52fbd = Gate-20 repro evidence, fbe6472e = old main) whose line reached main via #41 [MEASURED].

CI baseline [MEASURED, .github/workflows/check.yml@1203e291]: static job runs `make check` on every PR/push; QEMU job runs `make test-qemu-smoke` on PRs and `make test` (= tests/qemu/boot.sh, Makefile:231) on push, both on macos-15-intel.

| PR | fix summary | regression test verdict | evidence path/SHA | risk note |
|---|---|---|---|---|
| #35 | Reject overlapping loaded PE sections | **yes** — in-file `#[cfg(test)]` suite (6 tests, e.g. `rejects_overlaps_regardless_of_permissions_or_section_order`) + new Makefile `check-pe` target wired into `make check` → CI static job | kernel/src/pe.rs:155-245, Makefile:266-272 @891ff9dc | Low: host-runnable tests, plausibly fail on pre-fix pe.rs which accepted overlaps [INFERRED] |
| #36 | Reject undersized virtio-net common capabilities (`common_region` length bound) | **partial** — no unit test; boot-time self-check extended: `verify_network_parser_rejections` asserts undersized→None, minimal→Some; failure ⇒ `kernel_fail` "virtio network discovery boundary invalid" (lib.rs:357), so QEMU boot tests fail on pre-fix code | kernel/src/arch/x86_64/pci.rs:290,615-631; kernel/src/lib.rs:336-357 @4b87e9a2 | Assertion lives in kernel code, exercised only via QEMU CI; local `make check` cannot catch a future regression of this boundary |
| #37 | Release failed Linux init hierarchy frames (decouple `release_frames` from `valid`) | **no** — diff touches only gate doc + address_space.rs (name-only) | d33ee0f5, kernel/src/address_space.rs:641-665 | Invalid-init paths leak 6 hierarchy frames each; no CI assertion counts frame ownership, so a leak reintroduction passes boot.sh silently |
| #38 | Size getcwd output for maximum paths (`PATH_CAPACITY+1`→`+2`) | **no** — one-line change, no test files touched | fbe6472e, kernel/src/arch/x86_64/cpu.rs:22907 | A future off-by-one passes all CI; boot.sh hits getcwd only incidentally, never at max path length [INFERRED] |
| #41 | Drain stale virtio block recovery interrupts (17284060; `drain_pending_virtio_interrupt` in `arm_isolated_device_interrupt`) | **no** — no unit test; added workflow is branch-scoped and artifact-only; boot.sh/tools changes add OVMF-4M paths + artifact copies, no new assertions; Gate-20 doc relies on "the existing recovery sequence as its integration regression" | 17284060; .github/workflows/issue-14-linux-repro.yml; tests/qemu/boot.sh @1203e291; hdae/gates-todo/20-linux-native-volume-recovery.md:55-58 | Failure was Linux-host/QEMU-10.0.13–11.1.2 dependent (KVM/TCG); main CI QEMU is macos-15-intel, and the repro workflow triggers only on the feature branch — a drain regression can pass main CI [INFERRED] |
| #32 | test-only: payload padding rejected with valid digest | adds coverage of pre-range volume-format strictness; no in-range fix pairs (nothing in #35–#41 touches crates/) [MEASURED] | crates/volume-format/src/lib.rs @8a95643d | Not a fix → not a gap; characterization test, cannot fail without any in-range fix [INFERRED] |
| #33 | test-only: host geometry validation boundaries | same as #32 | crates/volume-format/src/lib.rs @c69d7cef | Same [INFERRED] |
| #34 | test-only: identical local-config commit performs no writes | same as #32 | crates/volume-service/src/lib.rs @dd2017b5 | Same [INFERRED] |
| 27370ba1 | bookkeeping merge, not a fix | n/a | parents dab52fbd/fbe6472e | none |

Gap ranking: #37 and #38 (zero coverage), #41 (coverage exists in spirit but is not wired to main CI), #36 (QEMU-gated kernel self-check only).

Doubt notes: #36 fail-without-fix is [INFERRED] — it assumes `discover_virtio_network` succeeds in CI boots so the extended self-check actually runs (lib.rs:336 calls it unconditionally, so plausible). #41: boot.sh could only catch a broken drain if the stale-interrupt condition reproduces under macOS TCG timing; the documented repro needed Linux QEMU versions, so [INFERRED] it would not. "Partial" for #36 reflects real, fix-coupled assertions, but they are runtime probes, not a dedicated test target.

## Commands used
- `git -C ... log origin/main --merges --oneline` (range enumeration; no PR #40 merge found)
- `git log --oneline -15 origin/main; git rev-parse origin/main`
- `git log --format='%h parents:%p %s' -1 27370ba1; ... -1 1203e291` (merge topology)
- `git diff <m>^1 <m> --name-only` and full diffs for 8a95643d c69d7cef dd2017b5 891ff9dc 4b87e9a2 d33ee0f5 fbe6472e 1203e291
- `git log origin/main --format='%h %s' --grep='#40'` (empty — negative finding)
- `git show 1203e291:.github/workflows/check.yml`, `:.../issue-14-linux-repro.yml`, `:Makefile` (grep of test/check targets), `:hdae/gates-todo/20-linux-native-volume-recovery.md`
- `git grep -n verify_network_parser_rejections 1203e291 -- kernel` (caller wiring: kernel/src/lib.rs:342)
- `git show 891ff9dc:kernel/src/pe.rs` (test function inventory)
- `git log --oneline origin/main -- tests/qemu/smoke.sh` (smoke.sh predates range: 640bc102)

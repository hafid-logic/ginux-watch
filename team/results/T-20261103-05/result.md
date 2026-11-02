# T-20261103-05 — Builder: failed-init frame-release regression (gate 22 / #37)

Executor: supervisor-as-builder (documented deviation: fork-push control kept by the
supervisor; role duties otherwise followed). User directive v2.2 §4. Fork-only —
nothing published upstream.

## Branch and contents [MEASURED]

- Fork `hafid-logic/ginux`, branch `builder/failed-init-frame-release-test`, base
  upstream main `95f8ef24`, heads: `dd482fb1` (change+test) → `b04e7a74` (rework after
  CI diagnosis). Final diff vs base: **+26 lines / 3 files** — `git diff --stat
  95f8ef24 b04e7a74` [MEASURED].
- Fork `main` synced to upstream `a7a41ae2` via `gh repo sync` (upstream merged #45
  during execution; builder branch is 1 commit behind, 1 ahead — diff = our commit
  only) [MEASURED: merge-base = 95f8ef24].
- **ONE change** (`kernel/src/address_space.rs`, +5): serial marker
  `ginux: Linux init hierarchy frames released after failed init` on the failed
  non-suspended path after `release_frames` — makes the gate-22 release observable.
- **ONE test** (`kernel/src/lib.rs` +16, `tests/qemu/boot.sh` +5): verification-boot
  self-test requires an invalid init attempt (`/nonexistent-init`) to return
  `LinuxProcessOutcome::Failed` and the boot to continue; boot.sh asserts the contract
  marker `ginux: failed-init hierarchy frame release verified`.

## Verification [MEASURED]

- Local: `cargo check -p ginux-kernel --target x86_64-unknown-none` PASS (25.24s).
- Actions `builder-verify.yml` run 1: **41541091690 = failure** (10.0.13 + 10.1.2) —
  diagnosis: the self-test's garbage payload hit the silent no-slot bail
  (`address_space.rs:242`), so the stage-level teardown where gate-22 lives was never
  reached; the `setup failed at stage` grep could never match. Artifact
  `logs-builder-qemu-10.0.13` (test.log:1315) [MEASURED].
- Actions run 2 (rework): **41542581308 = success, both legs** — make doctor/check/test
  0/0/0 on QEMU 10.0.13 AND 10.1.2 (TCG), `builder_sha=b04e7a74…`, `GINUX_KERNEL_OK`,
  `Boot test passed.`, contract marker present (artifact logs-builder-qemu-10.1.2).
- **FAILS-WITHOUT-THE-FIX property [OBSERVED]:** the contract test guards the failed-
  init outcome; the gate-22 release itself is NOT dynamically asserted end-to-end —
  the teardown is reachable only with a plan-passing/stage-failing executable in the
  published rootfs (fixture = extra build wiring, outside this card's one-change-one-
  test scope). Upstream gate-22 verified the fix by static control-flow inspection
  (hdae/gates-todo/22 verification plan). Remaining work: fixture design = minimal ELF
  passing `published_rootfs::process_plan` whose load segment violates the stage-2
  `directory_index in 2|3` window (address_space.rs:425 area) → stage failure →
  teardown → the new release marker becomes assertable in boot.sh.

## Deliverables

- Draft PR **inside the fork only**: https://github.com/hafid-logic/ginux/pull/1
  (draft, base hafid-logic:main, NOT upstream).
- Draft "I will work on X" comment (54 words) on upstream PR #37 prepared at
  `drafts/2026-11-03-pr37-workon.md` — **awaiting user approval, NOT posted**
  (v2.2 §4: no publish, no upstream PR).

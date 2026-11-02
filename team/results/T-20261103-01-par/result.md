# T-20261103-01 — Gap-finder: PR #37 "Release failed Linux init hierarchy frames"

Repo: gmkurtzer/ginux read-only clone `/home/z/my-project/work/ginux`; main = 95f8ef24. No builds, no network.

## 1. The fix [MEASURED]

PR head `eac4a784`; true PR diff = `git diff --stat 759cf2e2 eac4a784` (759cf2e2 = merge-base with pre-merge main 4b87e9a2; merge commit d33ee0f5): exactly 2 files — `kernel/src/address_space.rs` (+2/−3 numstat; the earlier +5/−3 came from --stat hunk grouping [MEASURED: git diff --numstat 759cf2e2 eac4a784]) and `hdae/gates-todo/22-failed-linux-init-frame-release.md` (+81). Code commit `b79cdb8a` "Release failed Linux init hierarchy frames" (2026-11-01T10:20:42-08:00, Signed-off-by Gregory M. Kurtzer), shown via `git show b79cdb8a`.

Mechanism, in `pub(crate) fn run_linux_init(init: &[u8])` (defined at line 249 on main), the non-suspended teardown after `LinuxElfResult`:

- Hunk @@ −641,8 +641,7: `let owned_released = valid && runtime_scrubbed && memory::release_frames(FrameOwner::KERNEL, [frames[0..6]])` → `let owned_released = runtime_scrubbed && memory::release_frames(...)`. The `valid` short-circuit removed.
- Hunk @@ −663,7 +662,7: success/diagnostics branch `if owned_released` → `if valid && owned_released`; outcome mapping (`LinuxProcessOutcome::Exited` only when valid) unchanged — invalid init still returns `Failed`.

Failure path closed: when the Linux runtime returned `valid=false` (kernel prints `ginux: Linux init setup failed at stage N`, address_space.rs:640 on main), the old `&&` chain short-circuited before `memory::release_frames`, so the six bootstrap page-table hierarchy frames (root, pdpt, directory, main, interpreter, runtime tables — `frames[0..6]`) leaked on every failed non-suspended init attempt [OBSERVED]. [OBSERVED] the suspended path (`valid && result.suspended`) returns earlier with ownership transfer and is untouched, per surrounding code at lines ~630-641. [MEASURED] `git diff eac4a784 origin/main -- kernel/src/address_space.rs` is empty: fix is on main 95f8ef24 unchanged (lines 644-645, 665).

## 2. The missing regression test

What it asserts (fails without the fix): after a forced invalid (non-suspended) Linux init attempt, the kernel releases all six hierarchy frames and still reports a failed outcome: a new serial marker emitted on the `!valid` path (e.g. `ginux: Linux init hierarchy frames released after failed init`), plus existing failed-domain serials; boot.sh asserts the marker and that the valid path is unchanged (no double release).

Natural home: **tests/qemu/boot.sh**. Justification [MEASURED]: Makefile `test: build-verification` → `@tests/qemu/boot.sh` (lines 231-233) and `check:` recipe (lines 272-303) run `cargo clippy --package ginux-kernel` but `cargo test` only for non-kernel crates; the sole kernel host-test hook is `check-pe` compiling `kernel/src/pe.rs` standalone (`git grep -n 'cfg(test)' origin/main -- kernel/` → only kernel/src/pe.rs:155). `run_linux_init` needs real CPU/QEMU execution, so a host `cargo test` is not viable; boot.sh is the repo's established kernel-behavior harness (grep-of-serial-markers, e.g. lines 794-800 IOMMU hierarchy, 1575/1659/1891 Linux hierarchy).

## 3. Evidence of absence on main 95f8ef24

Exact commands run in `/home/z/my-project/work/ginux` (all 0 hits → exit 1) [MEASURED]:

- `git grep -in 'owned_released' origin/main -- tests/ tools/` → 0 hits.
- `git grep -in 'release_frames' origin/main -- tests/ tools/` → 0 hits.
- `git grep -n 'setup failed at stage' origin/main -- tests/` → 0 hits: no test triggers or expects the failed-init path.
- `git grep -n 'cfg(test)\|#\[test\]' origin/main -- kernel/src/address_space.rs` → 0 hits (no host test hooks in the fixed file).
- `git grep -in 'teardown' origin/main -- tests/qemu/boot.sh` → hits only for virtio-net/VT-d teardown (lines 204, 296, 304, 313, 369); none for Linux-init frame teardown.
- Incidental vs regression coverage [MEASURED]: `git grep -in 'hierarchy' origin/main -- tests/` → 5 hits (boot.sh 194, 794, 1575, 1659, 1891), all asserting hierarchy *construction/replacement* on valid paths (IOMMU, page-table) — incidental; none exercises release on failed init, so no test fails without the fix [INFERRED].
- Gate inventory [MEASURED]: `git grep -n 'Gate 22\|frame release\|issue #26' origin/main -- hdae/` → only `hdae/gates-todo/22-failed-linux-init-frame-release.md` (still `gates-todo/`, review pending per its "Remaining work"). No gate in `gates-done/` covers it; no test hook referenced in gate file's verification plan beyond `make check`/`make test` (which contain no such assertion, per §2/§3).

## 4. Open-PR overlap (dump only)

Query [MEASURED]: python3 scan of `/home/z/my-project/work/data-wt/upstream-dump.jsonl` for numbers {39,45,46,47,48,49,50,51,52,53,54,56} with terms `release_frames, owned_released, frame release, gate 22, gate-22, issue 26, issue #26, hierarchy frames, failed linux init, linux init frame, 22-failed-linux-init` → **0 matching items**. Limitation [MEASURED]: dump items carry only `title, files, labels, state, timestamps, body_words/title_words (int counts)` — no body text — so titles/files/labels only; body-level overlap [UNVERIFIED].

Nearest overlaps by title/files/keywords (index.json) [MEASURED]: PR 46 "Enforce per-domain Linux memory limits" — touches `kernel/src/address_space.rs` + `tests/qemu/boot.sh`, gate 36-domain-memory-accounting (different mechanism: limits, not failed-init release); PR 53 "Stage rootfs exec before publication" — `address_space.rs` + boot.sh, keywords hierarchy/frames/replacement, gate 41 (hierarchy replacement on exec staging); PR 50/51 (kw teardown/failed/quarantine, gates 42/43) — DMA/IOMMU quarantine after failed teardown, adjacent theme, different files (`kernel/src/lib.rs`, `iommu.rs`). PR 45 has `state: "closed"` in the snapshot despite the candidate list. **None adds a failed-init frame-release regression test** [INFERRED from titles/files/keywords only].

## 5. Builder feasibility

[MEASURED] `make check` (Makefile 272-303) compiles `address_space.rs` via `cargo clippy --package ginux-kernel --target x86_64-unknown-none -- -D warnings` (a one-line boolean guard change is clippy-clean) but runs no kernel unit tests. [MEASURED] `make test` = `build-verification` (cargo build ginux-boot --features verification-boot) + `tests/qemu/boot.sh` (QEMU 10.0.13/10.1.2 per card/protocol — not verified locally, no builds). So one fix + one test on a fork branch: the fix compiles under `make check`; the test added to **`tests/qemu/boot.sh`** runs under `make test`. [INFERRED] caveats: the kernel must first emit a success-side marker after releasing frames on the invalid path (today it only prints when `!owned_released`, address_space.rs:654-656), and boot.sh needs a scenario forcing invalid init — boot.sh already has corrupt-media/reboot boot phases (`corrupt_output_file`, lines ~30-45) to host it. Without these, `make test` does not fail without the fix (per §3 greps) [INFERRED].

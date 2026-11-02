# T-20261103-01 — Gap finder: merged PR #37 (failed Linux init frame release, gate 22)

Verdict: **real fix, merged, but no regression test guards it** — `make check`/`make test` would pass if the short-circuit were reintroduced. [INFERRED from §3's MEASURED 0-hit inventory]

## 1. THE FIX [MEASURED]

Commits on branch `pr-37` (= merged PR #37 head `eac4a784`): `b79cdb8a` "Release failed
Linux init hierarchy frames" touched `kernel/src/address_space.rs` (+5/−3) and added
`hdae/gates-todo/22-failed-linux-init-frame-release.md`; `eac4a784` updated only the gate
file. Command: `git show --stat --oneline b79cdb8a eac4a784` in
/home/z/my-project/work/ginux. Diff base is `b79cdb8a^` (= `759cf2e2`, an older main);
merge-base of `pr-37` and `origin/main` is `eac4a784` itself, proving both commits are
ancestors of main `95f8ef24` [MEASURED, `git merge-base pr-37 origin/main`].

Mechanism, inside `run_linux_init` (`kernel/src/address_space.rs`, function spans lines
249–687 at `pr-37`; diff command `git diff b79cdb8a^ eac4a784 -- kernel/src/address_space.rs`):
- Lines 644–651: release guard changed from
  `owned_released = valid && runtime_scrubbed && memory::release_frames(FrameOwner::KERNEL, frames[0..6])`
  to `owned_released = runtime_scrubbed && memory::release_frames(...)`. Pre-fix, when the
  runtime returned `valid == false`, `&&` short-circuiting skipped all six bootstrap
  page-table hierarchy frame releases (leak on every failed init path).
- Line 665: outcome guard changed from `if owned_released` to `if valid && owned_released`,
  so invalid execution still returns `LinuxProcessOutcome::Failed` and skips runtime
  diagnostics. Suspended path (ownership transfer, ~lines 625–632) untouched, matching the
  gate file's non-goals [MEASURED, gate file at pr-37].

Failure path closed: non-suspended invalid Linux init now releases its six launcher-owned
hierarchy frames instead of leaking them, and stays a Failed exit.

## 2. THE MISSING REGRESSION TEST [INFERRED from MEASURED wiring]

What it asserts: a deliberately invalid (verification-boot) Linux init attempt must
(a) emit a success marker analogous to existing release markers (e.g. pattern of
`ginux: owned root frames scrubbed and released`, boot.sh:1520) after releasing the six
hierarchy frames, (b) leave `memory::owner_live_frame_count(FrameOwner::KERNEL)` back at
its pre-launch value — assertion style already used at
`kernel/src/address_space.rs:1563` (`frame_count_restored`), and (c) still report the
Failed outcome (e.g. `ginux: Linux init setup failed at stage N`, address_space.rs:640);
without the fix, (a)/(b) fail because release is skipped. [INFERRED]

Natural home: **`tests/qemu/boot.sh`** (the `make test` scenario, Makefile:230–231), which
asserts hundreds of serial markers and delegates Linux-runtime categories to
`tests/qemu/check-linux-runtime.sh` (boot.sh:165) — a "failed init frame release" category
fits there. Host `cargo test` cannot cover it: `make check` runs `cargo test` only for
10 host packages (Makefile:279–298); `ginux-kernel` is no_std for
`x86_64-unknown-none`, absent from that list, and
`kernel/src/address_space.rs` has zero `#[cfg(test)]` blocks [MEASURED, §3]. One gap: no
harness hook deliberately launches an invalid Linux init
(`git grep -in "deliberate\|intentionally invalid\|rejection probe" origin/main -- kernel/src/address_space.rs`
→ 0 hits), so a small negative-probe hook in the verification-boot path is also needed.
[MEASURED + INFERRED]

## 3. EVIDENCE OF ABSENCE on main 95f8ef24 [MEASURED]

All commands `git grep … origin/main` in /home/z/my-project/work/ginux; 0 hits unless noted:
- `git grep -in "release_frames" origin/main -- tests/` → 0
- `git grep -in "owned_released" origin/main -- tests/ Makefile` → 0
- `git grep -in "runtime_scrubbed" origin/main -- tests/` → 0
- `git grep -in "FrameOwner" origin/main -- tests/` → 0
- `git grep -in "setup failed at stage" origin/main -- tests/` → 0
- `git grep -in "gate-22\|gate 22\|issue-26" origin/main -- tests/ Makefile` → 0
- `git grep -n "cfg(test)\|#\[test\]" origin/main -- kernel/` → only
  `kernel/src/pe.rs` (6 tests, lines 155–238); none in `address_space.rs`, none about
  frame release.
- `git grep -in "Linux init" origin/main -- tests/qemu/boot.sh` → 3 hits (boot.sh:2570,
  2856, 2906), all positive-path markers (init arrays, environment vector, namespace
  identity) — incidental, not failed-path frame release.
- `git grep -in "hierarchy" origin/main -- tests/` → 8 hits, all IOMMU/child-hierarchy
  markers — incidental.

Conclusion: no test on main asserts hierarchy-frame release on the failed init path; the
PR's own gate file lists only "static control-flow inspection" plus the generic suites as
verification [MEASURED, gate file "Verification plan" section]. No regression test fails
without this fix. [INFERRED from the 0-hit inventory]

## 4. OPEN-PR OVERLAP (dump only) [MEASURED]

Source: /home/z/my-project/work/data-wt/index.json + upstream-dump.jsonl
(2026-11-02T22:05:39Z, 56 items). For all 12 candidate PRs, no title/keyword hit for:
leak, release_frames, frame release, hierarchy frame, gate-22/22, issue 26/-26,
owned_released, runtime_scrubbed, failed linux, invalid init (python filter; the dump
stores bodies as word counts only — limitation). Closest overlaps by files:
- **#46** "Enforce per-domain Linux memory limits": touches `kernel/src/address_space.rs`,
  `kernel/src/memory.rs` (where `release_frames` lives), `tests/qemu/boot.sh`, gate-36;
  keywords frame/kernel/linux/memory — same memory-accounting neighborhood, no evidence it
  adds the failed-init test.
- **#50** "Quarantine DMA after failed runtime teardown" and **#51** "Quarantine IOMMU
tables after failed rollback" (both boot.sh): adjacent "failed teardown" theme, DMA/IOMMU
not Linux-init page tables.
- #48/#49/#53/#54 touch `address_space.rs` (secret-page copies, SMP mprotect, rootfs exec
staging, overflow checks) — unrelated mechanisms.
Query recorded above; **no open PR adds this regression test per dump metadata**. #45
shows `state: closed` in the dump [OBSERVED].

## 5. BUILDER FEASIBILITY [INFERRED from MEASURED wiring]

Yes. `make check` (Makefile:262–298) compile-checks the kernel via clippy
(`x86_64-unknown-none`, −D warnings), catching syntax/arch regressions in address_space.rs;
`make test` (Makefile:230–231) = `build-verification` (builds ginux-boot with
`--features verification-boot`, Makefile:141) + `tests/qemu/boot.sh` under the pinned QEMU
(10.0.13/10.1.2 per card), exercising the new marker. Exact test
file: **`tests/qemu/boot.sh`** (assertions) + `tests/qemu/check-linux-runtime.sh`
(category); kernel-side marker near the address_space.rs:1563 diagnostics. No local
builds (protocol) — runtime behavior [UNVERIFIED].

## Negative results
- No `#[cfg(test)]` in kernel/src/address_space.rs on main [MEASURED, §3].
- No tests/ or Makefile reference to release_frames/owned_released/gate-22/issue-26 [§3].
- No deliberate invalid-init probe hook in address_space.rs [§2].
- No dump PR body text; term search over title+keywords only [§4].

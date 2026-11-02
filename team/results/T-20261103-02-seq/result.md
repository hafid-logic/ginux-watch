# T-20261103-02-seq — gap-finder, PR #38 "Size getcwd output for maximum paths" (independent rerun)

Repo state: `git -C /home/z/my-project/work/ginux merge-base pr-38 origin/main` → `1973f80c` = the PR head itself, and `git merge-base --is-ancestor 1973f80c origin/main` passes [MEASURED]. So PR #38 is already an ancestor of main `95f8ef24`; the brief's "diff pr-38 vs merge-base" is empty by construction. The fix is therefore measured as commit `24eea9cf` vs its parent `759cf2e2` [MEASURED: `git show --stat 24eea9cf`].

## 1. THE FIX [MEASURED]

- PR #38 = 2 commits on `759cf2e2`: `24eea9cf` "Size getcwd output for maximum paths" (hdae/gates-todo/23-getcwd-maximum-path-capacity.md +74 lines new; kernel/src/arch/x86_64/cpu.rs 1 line changed) and `1973f80c` "Record Gate 23 pull request delivery" (gate doc +8/-3 only, no code) [MEASURED: `git show --stat 24eea9cf 1973f80c`].
- The code change is one line in `fn linux_getcwd(address: u64, capacity: u64) -> u64` (fn at cpu.rs:22905 on both `1973f80c` and origin/main), hunk `@@ -22904,7 +22904,7 @@`: `let mut output = [0_u8; crate::linux_overlay::PATH_CAPACITY + 1];` → `... PATH_CAPACITY + 2];` [MEASURED: `git show 24eea9cf -- kernel/src/arch/x86_64/cpu.rs`; line confirmed at cpu.rs:22907 on origin/main via `git grep -n "PATH_CAPACITY + [12]" origin/main -- kernel/src/arch/x86_64/cpu.rs`].
- Mechanism: `PATH_CAPACITY = 256` (kernel/src/linux_overlay.rs:9) [MEASURED]. The staging array must hold leading `/` (1) + up-to-256-byte copied cwd + NUL (1) = `PATH_CAPACITY + 2`. `required = length + 1` (cpu.rs:22945 region); with the old 257-byte array and a 256-byte copied path, `required` = 258 and `copy_to_linux_user(address, &output[..required])` slices past the array → runtime panic in-guest. Failure closed: gate-23 / issue #21, recorded in the dump as "getcwd off-by-one: 257-byte output buffer vs 258-byte requirement" [MEASURED: `rg -i getcwd /home/z/my-project/work/data-wt/upstream-dump.jsonl`; gate doc Evidence section]. `ERANGE` (capacity < required) and `EFAULT` (copy failure) paths are unchanged [OBSERVED: function body read on origin/main cpu.rs:22905-22951].

## 2. THE MISSING REGRESSION TEST

What a failing-without-fix test asserts [INFERRED from mechanism, grounded in the function body]: with cwd state resolved to a 256-byte (`PATH_CAPACITY`) copied path, `getcwd(buf, cap=258)` returns 258 and writes `/` + path + NUL; `cap=257` → `ERANGE`; invalid user pointer → `EFAULT`; and no kernel panic. Without the fix the happy path panics (258-byte slice of a 257-byte array), so the test fails.

Natural home: NOT a host `cargo test` on the syscall layer — ginux-kernel is `#![no_std]` (kernel/src/lib.rs:1) compiled for `x86_64-unknown-none` and `make check` never runs `cargo test` for it (Makefile:272, `cargo test` lines 279-298 cover native-abi…volume-service only; ginux-kernel gets clippy only). The only kernel-crate host test is kernel/src/pe.rs, compiled standalone by `check-pe` via `rustc --edition=2021 --test` [MEASURED: Makefile]. The behavioral home is in-guest QEMU: extend the `test linux` command family in control-plane/runtime/src/main.rs (see §5) with a dynamic max-path getcwd case, exercised via `make test` (tests/qemu/boot.sh) or `tests/qemu/linux-abi-report.sh` [INFERRED].

## 3. EVIDENCE OF ABSENCE on main 95f8ef24

All commands run against the read-only clone; exact commands + results [MEASURED]:
- `git grep -l -i getcwd origin/main` → hits ONLY in docs/LINUX-COMPATIBILITY.md, hdae/gates-todo/23-…md, kernel/src/arch/x86_64/cpu.rs, kernel/src/arch/x86_64/cpu/linux_abi.rs, kernel/src/arch/x86_64/cpu/linux_syscall.rs, specs/kernel/linux-elf-v0.md, specs/kernel/linux-syscall-v0.md. Zero test files.
- `git grep -l -i getcwd origin/main -- tests/` → rc=1, 0 hits (tests/ = 18 QEMU/shell scenarios, no getcwd).
- `git grep -n -i "path_capacity\|getcwd" origin/main -- crates/ control-plane/` → rc=1, 0 hits: no host crate or guest-runtime code references the mechanism.
- `git grep -n "cfg(test)" origin/main -- kernel/src/` → single hit kernel/src/pe.rs:155; cpu.rs has no unit tests.
- `git show origin/main:control-plane/runtime/build.rs` → the in-guest `test linux syscall` ledger is statically generated from docs/LINUX-COMPATIBILITY.md (`"Partial"|"Unsupported"|"Missing" => "Fail"`), and that matrix row is `| 79 | getcwd | Partial |` (line 541) — a static label, not an executed check [MEASURED].
- Conclusion [INFERRED]: no existing test fails without the fix; triggering the panic needs a 256-byte cwd, which nothing creates (0 hits for chdir/mkdir in control-plane/runtime/src/main.rs). The gate doc confirms the bug was found by boundary inspection, not by a failing test [OBSERVED: gate doc "Evidence"].

## 4. OPEN-PR OVERLAP (dump only)

Query: regex `getcwd|PATH_CAPACITY|path.?capacity|cwd|gate.?23|issue.?21|maximum.?path|staging.?buffer` over `index.json` items for open PRs 39,46,47,48,49,50,51,52,53,54,56 → **NONE** for every PR [MEASURED: python3 scan of /home/z/my-project/work/data-wt/index.json, generated 2026-11-02T22:05:39Z]. Raw `rg -c -i "getcwd|PATH_CAPACITY" upstream-dump.jsonl` → 2 lines: issue #21 and PR #38 only. PR #56 touches kernel/src/arch/x86_64/cpu.rs (TSC clock) but has zero keyword overlap. Note: #45 is `closed` in the dump. No open PR adds such a test or touches the mechanism.

## 5. BUILDER FEASIBILITY (short)

The fix path is only reachable in-guest: `linux_getcwd` lives in the no_std kernel crate, is dispatched at kernel/src/arch/x86_64/cpu/linux_syscall.rs:939 (`LINUX_GETCWD_SYSCALL = 79`, linux_abi.rs:111), and depends on `X86_RUNTIME` atomics + overlay/rootfs state; host `cargo test` does not build ginux-kernel [MEASURED]. A meaningful behavioral host-side test is **not reachable** as one change + one test. Two partial options [INFERRED]: (a) a compile-time staging-arithmetic assertion (named const + `const` assert) in kernel/src/arch/x86_64/cpu.rs, caught by `make check`'s clippy pass on ginux-kernel (Makefile:277) — but it guards arithmetic only, not ERANGE/EFAULT behavior; (b) the real regression test belongs in control-plane/runtime/src/main.rs + tests/qemu/linux-abi-report.sh under `make test` — more than a one-line change since the runtime has no chdir/mkdir today.

**Verdict**: fix is merged and correct, but gate-23 ships with zero regression coverage anywhere; no open PR covers the gap; a QEMU-guest getcwd boundary test is the actionable follow-up.

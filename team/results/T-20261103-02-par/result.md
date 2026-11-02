# T-20261103-02 — Gap-finder: PR #38 "Size getcwd output for maximum paths"

Repo: hafid-logic/ginux-watch, worker w2. Upstream data: read-only clone `/home/z/my-project/work/ginux` and snapshot `/home/z/my-project/work/data-wt/{index.json,upstream-dump.jsonl}` (2026-11-02T22:05:39Z). No network, no builds.

## 1. The fix [MEASURED]

- [MEASURED] `merge-base pr-38 origin/main` = `1973f80c` (recorded command: `git -C /home/z/my-project/work/ginux merge-base pr-38 origin/main`) → main `95f8ef24` already contains PR #38; the pre-fix base is `759cf2e2` (parent of correction commit `24eea9cf`; recorded command: `git -C /home/z/my-project/work/ginux log --oneline -3 pr-38`).
- [MEASURED] Diff (recorded command: `git -C /home/z/my-project/work/ginux diff 759cf2e2 pr-38 -- kernel/`): exactly one code line changed, `kernel/src/arch/x86_64/cpu.rs` line 22907, inside `fn linux_getcwd` (lines 22905–22944 on pr-38/main): staging buffer `[0_u8; crate::linux_overlay::PATH_CAPACITY + 1]` → `[0_u8; crate::linux_overlay::PATH_CAPACITY + 2]`. Plus a new 79-line gate doc `hdae/gates-todo/23-getcwd-maximum-path-capacity.md` (`git diff --stat 759cf2e2 pr-38`: 2 files, +80/−1).
- [MEASURED] Mechanism: `PATH_CAPACITY = 256` (`kernel/src/linux_overlay.rs:9`). `linux_getcwd` writes `'/'` at `output[0]` (cpu.rs:22908) and copies the ≤256-byte cwd via `linux_overlay::copy_path` (linux_overlay.rs:465–476) or `published_rootfs::copy_path` into `output[1..]`; `required = length + 1` (cpu.rs:22940) reserves the trailing NUL byte that remains 0. A 256-byte path needs `1 + 256 + 1 = 258` bytes; the old 257-byte array made `&output[..required]` (cpu.rs:22944) out-of-range → kernel panic. Matches dump issue #21 title "getcwd off-by-one: 257-byte output buffer vs 258-byte requirement on 256-char paths — kernel panic" [OBSERVED, upstream-dump.jsonl item 21].
- [MEASURED] Contract preserved: caller-buf `ERANGE` when `capacity < required` (cpu.rs:22941–22943); `EFAULT` via `copy_to_linux_user` failure (cpu.rs:22944–22945, impl at cpu.rs:38956–38963). `copy_path` itself is bounds-safe (`get_mut(..len)`), so only the final slice was the panic site.

## 2. The missing regression test [INFERRED]

- [INFERRED] A test that fails without the fix: chdir into a canonical cwd of exactly 256 bytes, then `getcwd(buf, 258)` must return 258 containing `'/' + path + NUL`, and `getcwd(buf, 257)` must return `ERANGE`. Without the fix the 256-byte-path case panics at cpu.rs:22941 instead of returning 258.
- [INFERRED] Natural home: an in-guest QEMU scenario (new `tests/qemu/getcwd-max-path.sh`, sibling of the 17 existing scenarios under `tests/qemu/`, e.g. `boot.sh`, `alpine-shell.sh`) because the code under test is freestanding kernel code. `make test` = `build-verification` + `tests/qemu/boot.sh` (Makefile:231–232 on main), so a new scenario needs wiring there or its own target.
- [INFERRED] A host `cargo test` of `linux_getcwd` directly is not reachable: the function reads `X86_RUNTIME` statics and writes guest memory via `raw_copy_to_user` (cpu.rs:38956–38963), and ginux-kernel builds for `x86_64-unknown-uefi/none` (Makefile TARGET, line 3). Host unit-test precedent is `check-pe` (`rustc --edition=2021 --test kernel/src/pe.rs`, Makefile:267–270) — it works because `pe.rs` is standalone; `linux_getcwd` is not.

## 3. Evidence of absence on main 95f8ef24 [MEASURED]

Exact recorded commands, all with 0 hits (git grep exit=1):

- `git -C /home/z/my-project/work/ginux grep -n -i getcwd 95f8ef24 -- tests/` → 0 hits.
- `git -C /home/z/my-project/work/ginux grep -n -i erange 95f8ef24 -- tests/` → 0 hits.
- `git -C /home/z/my-project/work/ginux grep -n PATH_CAPACITY 95f8ef24 -- tests/` → 0 hits.

[MEASURED] Full-tree `getcwd` hits on main are implementation/docs only: `kernel/src/arch/x86_64/cpu.rs:11274,22905`, `kernel/src/arch/x86_64/cpu/linux_syscall.rs:939`, `docs/LINUX-COMPATIBILITY.md:541` ("Partial"), `specs/kernel/linux-syscall-v0.md:384,1970`, `specs/kernel/linux-elf-v0.md:839`, and the gate doc. [MEASURED] Unit-test surface: only `kernel/src/pe.rs` contains `cfg(test)` (`git grep -l "cfg(test)" 95f8ef24 -- kernel/src`). Conclusion: no existing test exercises `getcwd` at capacity; reverting the fix would not fail anything on main.

## 4. Open-PR overlap (dump only) [MEASURED]

Query (recorded): python scan of `index.json` items 39,45,46,47,48,49,50,51,52,53,54,56 + full-text scan of `upstream-dump.jsonl` for `getcwd`/`erange`. Results:

- getcwd/erange hits: only merged PR #38 and open source issue #21 (`files: []`, still unattached) — [OBSERVED].
- Touching `kernel/src/arch/x86_64/cpu.rs`: PRs 46, 48, 53, 54, 56. PR 54 "Enable overflow checks in release builds" (keyword "capacity") merely shares the file; none of the 12 open PRs mentions getcwd, ERANGE, or adds this regression test.
- [UNVERIFIED] Line-level overlap: the dump provides per-item `files`/title/keywords only, no diffs or bodies, so whether PR 54 edits the same cpu.rs lines cannot be confirmed from the snapshot.

## 5. Builder feasibility [INFERRED]

- Not a clean "one change + one host test": the fixed code path is kernel-only, reachable in-guest; say so explicitly — a host-side test of the actual `linux_getcwd` would require extracting the sizing/copy logic into a standalone module (pe.rs-style, exercised via `check-pe` in `make check`). Today that refactor does not exist.
- Feasible shape: one in-guest scenario (`tests/qemu/getcwd-max-path.sh`) plus wiring in `tests/qemu/boot.sh`/Makefile `test:` target, exercised by `make test` (QEMU 10.1.2/TCG per gate doc) — this matches the repo's regression style. [UNVERIFIED] Whether the in-guest runtime can create a 256-byte cwd (overlay `chdir` path building) needs a QEMU run; no builds were performed here per protocol.
- Sibling check [MEASURED]: `git grep -n "PATH_CAPACITY + 1" 95f8ef24 -- '*.rs'` finds one other use, `kernel/src/published_rootfs.rs:240` — an intentional overflow sentinel (`unwrap_or(PATH_CAPACITY+1)` then `> PATH_CAPACITY` rejection), not the same bug; no action.

**Verdict:** fix is correct and minimal but regression-test coverage on main is zero; best gap to close is an in-guest max-path getcwd scenario (ERANGE boundary + no panic), with a standalone host-test refactor as the alternative.

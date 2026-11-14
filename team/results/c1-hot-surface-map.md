# C-1 Hot Surface Map — ginux (gmkurtzer/ginux) last 60 merged PRs

## 1. Method + base SHA [MEASURED]

- Base measured at: `origin/main` = `285d025b7f8bcad0784585dcfbd23cada4643408`, commit time `2026-11-13T21:30:14-08:00` (= 2026-11-14T05:30:14Z). Evidence: `git rev-parse origin/main` + `git log -1 --format="%H %cI"` in `/home/z/my-project/work/upstream-ginux` (existing clone, no new clone, no GitHub API).
- PR identification [MEASURED]: `git log --merges --first-parent -E --grep="Merge (pull request|PR) #" -60 --format="%H|%cI|%s" origin/main`. Two merge styles exist: GitHub-style `Merge pull request #N from ...` (35/60) and `Merge PR #N: <summary>` (25/60) [MEASURED: grep of first-parent log; 136 PR merges total in history].
- Squash-merged PRs: none found [MEASURED: `git log --first-parent --no-merges --format="%s" origin/main | grep "(#N)"` returns 0 rows in the whole history]. Direct non-PR pushes DO exist on main (e.g. HEAD commit `285d025` "fix(init): track standard descriptors by backing object", plus non-PR merge commits like `2b0b020` "Merge upstream main into configured mkdirat" which introduced `crates/security-fuzzer` + `tests/fuzz-corpus/`) [MEASURED: `git log --diff-filter=A -- crates/security-fuzzer`]; these carry no PR number and are excluded from the 60.
- Changed files per PR [MEASURED]: `git diff --name-only <merge>^1 <merge>` (first-parent diff; blobs fetched lazily from origin). Note: `git diff-tree --no-commit-id --name-only -r --first-parent` returns EMPTY for merge commits in this repo setup — use `git diff ^1` instead [MEASURED].
- Area / defect / pure-vs-runtime columns are [INFERRED] from the measured changed-file lists + merge-commit titles/bodies (`git log -1 --format=%b <merge>`); short diff snippets read for ambiguous cases (e.g. `store_tracee_u32`, `audit_write`, `wait`).
- "Test added" [MEASURED]: added-line scan of the PR diff (`^\+.*#\[test\]`, `^\+.*(def test_|check\(|assert|expect_)`) + changed `scripts/test-*` / `tests/fixtures/*` / `tests/fuzz-corpus/*` paths.
- Merge-date normalization: all dates below converted to UTC via Python `datetime.fromisoformat(...).astimezone(utc)` over the same git output [MEASURED].

## 2. Per-PR table (60 rows, newest first)

Legend — pure: P = pure logic testable without a VM; M = mixed (pure core + runtime glue); R = runtime/VM-or-native interaction. test: U = Rust `#[test]` added; Y = Python/shell/fixture runtime test added; N = no test. Defect vocabulary: semantics = wrong syscall semantics, TOCTOU = race/TOCTOU, bounds = missing bounds/format check, enforce = security/policy not enforced, leak = resource/leak-on-error, ux = API/UX, perf = performance, refactor = refactor/docs.

| PR | merged (UTC) | area | defect | pure | test |
|----|----|----|----|----|----|
| 289 | 2026-11-14 | network | enforce: send destination not snapshotted before use (TOCTOU) | R | Y |
| 278 | 2026-11-14 | descriptors | enforce: console descriptor I/O unmediated | R | Y |
| 288 | 2026-11-14 | descriptors | semantics: native descriptor table not authoritative (dup/close bookkeeping) | R | Y |
| 287 | 2026-11-14 | clone | enforce: configured native clone policy ignored | R | Y |
| 286 | 2026-11-14 | pid | semantics: host tid leaked via set_tid_address result | R | Y |
| 281 | 2026-11-14 | pidfd | semantics: thread pidfd must give ENOENT (was misclassified) | R | N |
| 280 | 2026-11-14 | waitid | leak: traced threads not reaped on native failure | R | Y |
| 282 | 2026-11-14 | other-packaging | ux: Gate 26 RPM packaging (feature) | M | U+Y |
| 274 | 2026-11-13 | pid | semantics: translated native pid selectors lost | R | Y |
| 277 | 2026-11-13 | contract | refactor: classify all mediated systemd audit surfaces | P | U |
| 276 | 2026-11-13 | clone | TOCTOU: interrupted clone3 replay not restarted (EINTR) | R | Y |
| 275 | 2026-11-13 | waitid | leak/race: paranoid yield broker killed by signals | R | Y |
| 273 | 2026-11-13 | other-cli | ux: Gate 25 declarative CLI framework (feature) | M | U+Y |
| 272 | 2026-11-13 | instance | bounds: extra args accepted to fixed-arity runtime commands | R | Y |
| 267 | 2026-11-13 | procfs | TOCTOU: reaped service credentials lost for journal output | R | Y |
| 266 | 2026-11-13 | procfs | semantics: sysinfo ignored configured virtual memory | R | Y |
| 271 | 2026-11-13 | procfs | semantics: workload identity misreported | R | Y |
| 270 | 2026-11-13 | tests | ux: security fuzzer build not portable (tooling) | R | N |
| 269 | 2026-11-13 | docs | docs: stale ABI contract coverage table | R | N |
| 268 | 2026-11-13 | contract | enforce: native audit records incomplete | R | Y |
| 248 | 2026-11-13 | tests | bounds: virtual cgroup regression coverage lost after virtualization | R | Y |
| 247 | 2026-11-13 | waitid | leak: waitid children never reclaimed | R | Y |
| 246 | 2026-11-13 | pidfd | semantics: pidfd info ioctl not virtualized | R | Y |
| 245 | 2026-11-13 | clone | TOCTOU: clone3 arguments mutated during inspection, not snapshotted | R | Y |
| 244 | 2026-11-13 | pidfd | semantics: pidfd wait handling wrong | R | Y |
| 243 | 2026-11-13 | contract | enforce: launch contract not enforced across hooks | M | U+Y |
| 242 | 2026-11-13 | waitid | semantics: native SIGCHLD not delivered | R | Y |
| 238 | 2026-11-13 | descriptors | enforce: signal-driven I/O (F_SETOWN/FIOASYNC) accepted | M | U+Y |
| 236 | 2026-11-13 | paths | enforce: inherited host directories reachable from instance | R | Y |
| 234 | 2026-11-13 | waitid | semantics: orphaned children not adopted (reparenting) | M | U+Y |
| 256 | 2026-11-09 | CI | ux: docs-only changes re-trigger full CI | R | Y |
| 254 | 2026-11-09 | contract | ux: Gate 12.5 contract maintenance lock (feature) | R | Y |
| 253 | 2026-11-09 | instance | ux: Gate 12.25 top-level instance CLI (feature) | R | Y |
| 252 | 2026-11-09 | procfs | ux: Gate 12.1 in-memory procfs/sysfs (feature) | R | Y |
| 251 | 2026-11-09 | contract | ux: Gate 12 contract/network configuration simplification | M | U+Y |
| 249 | 2026-11-09 | contract | perf: Gate 11 syscall dispatch characterization/optimization | M | U+Y |
| 237 | 2026-11-07 | config | ux: Gate 10.5 intuitive self-contained contract config | M | U+Y |
| 235 | 2026-11-07 | instance | refactor: Gate 10.25 domains renamed to instances | R | Y |
| 231 | 2026-11-06 | contract | ux: Gate 10 configurable contract + audit (feature) | M | U+Y |
| 229 | 2026-11-06 | network | ux: Gate 9.75 domain spec + network controls (feature) | M | U+Y |
| 228 | 2026-11-06 | docs | docs: close Gates 9/9.5 (bookkeeping) | R | Y |
| 221 | 2026-11-06 | waitid | semantics: wait4 status store must fail EFAULT like Linux | R | Y |
| 218 | 2026-11-05 | vfs | TOCTOU: symlinks resolved after parent components | P | U |
| 217 | 2026-11-05 | vfs | TOCTOU/lifetime: unlinked files freed before last close | P | U |
| 216 | 2026-11-05 | vfs | leak-on-error: failed open destroyed the file contents | P | U |
| 215 | 2026-11-05 | pid | enforce: host tid leaked via set_tid_address and PI futexes | R | U+Y |
| 213 | 2026-11-05 | waitid | semantics: SIGINT/SIGTERM not delivered to task parked in wait4 | M | U+Y |
| 211 | 2026-11-05 | instance | leak: gate1 payload not killed when ptrace setup fails | R | Y |
| 209 | 2026-11-05 | other-scripts | TOCTOU: cached Rocky rootfs reused without hash verify | R | N |
| 206 | 2026-11-05 | descriptors | semantics: descriptor aliases bypassed stdio write rule | M | U+Y |
| 204 | 2026-11-05 | clone | refactor/regression: native loop lost control of fork/signal-stops/int 0x80 | R | Y |
| 201 | 2026-11-05 | other-scripts | TOCTOU: host image cached before verification | R | N |
| 199 | 2026-11-05 | other-scripts | TOCTOU: booted image not the verified image | R | N |
| 197 | 2026-11-05 | instance | ux: domain/vfs input errors not reported via domain_fail | R | Y |
| 195 | 2026-11-05 | tests | bounds: inherited descriptors reached the tracee (coverage gap) | R | Y |
| 193 | 2026-11-05 | vfs | bounds: GNU sparse tar entries misindexed instead of rejected | P | Y |
| 191 | 2026-11-05 | pid | semantics: sigprocmask/fork/exec signal-state rules violated | P | U |
| 189 | 2026-11-05 | other-runtime | bounds: initial stack misaligned, auxv not NUL-terminated | P | U |
| 187 | 2026-11-05 | contract | bounds: audit record split at byte budget instead of dropped | P | Y |
| 185 | 2026-11-05 | waitid | TOCTOU: death of tasks killed in supervised stop not awaited | M | Y |

## 3. Per-area aggregates [MEASURED counts; pure/test columns INFERRED from diff scans]

| area | PRs | pure(P)/mixed(M)/runtime(R) | tests added | notes |
|----|----|----|----|----|
| waitid | 8 | 0P/4M/4R | 8/8 | defects: 4 semantics, 3 TOCTOU/leak, 1 race; all runtime-tested only |
| contract | 8 | 1P/5M/2R | 8/8 | mostly Gate features (10/10.5/11/12/12.5); 1 pure (audit classify) |
| instance | 5 | 0P/0M/5R | 4/5 | CLI UX + renames + error reporting |
| descriptors | 4 | 0P/2M/2R | 4/4 | ALL logic in ginux-init (0 unit tests) |
| clone | 4 | 0P/0M/4R | 4/4 | clone3 snapshot/EINTR/policy — all runtime-tested |
| pid | 4 | 1P/0M/3R | 4/4 | tid virtualization/leaks; 1 pure (signal-state rules) |
| vfs | 4 | 3P/0M/1R | 4/4 | 3 of 4 are pure single-file fixes in ginux-vfs |
| procfs | 4 | 0P/0M/4R | 4/4 | sysinfo/journal/cgroup/identity |
| pidfd | 3 | 0P/0M/3R | 2/3 | PR 281 = no test at all |
| tests | 3 | 0P/0M/3R | 3/3 | coverage-gap PRs themselves |
| other-scripts | 3 | 0P/0M/3R | 0/3 | image verify TOCTOU trio, no tests |
| network | 2 | 0P/1M/1R | 2/2 | |
| docs | 2 | — | 0/2 | |
| paths | 1 | 0P/0M/1R | 1/1 | |
| config | 1 | 0P/1M/0R | 1/1 | |
| CI | 1 | 0P/0M/1R | 1/1 | |
| other-cli | 1 | 0P/1M/0R | 1/1 | |
| other-runtime | 1 | 1P/0M/0R | 1/1 | |
| other-packaging | 1 | 0P/1M/0R | 1/1 | |

Totals: 60 PRs; test surface touched (test/fixture/fuzz-corpus file changed OR inline Rust `#[test]` added) = 55/60 [MEASURED: 49 PRs touched `scripts/test-*|tests/|scripts/fuzz-*` files; 18 PRs added Rust `#[test]` lines (12 of them overlapping)]. Truly no test change: 5 PRs — 281, 269, 209, 201, 199. Only 18/60 added Rust unit tests; the other ~37 extended Python/shell/fixture runtime tests. [MEASURED: /tmp/c1_testkinds3.txt + file-list scan]

## 4. Top-3 hot regions

### 4.1 waitid / process reaping + signal delivery (TOP)
- Why hot: 8 fixes in 9 days (most of any area) — orphan adoption (#234), SIGCHLD delivery (#242), EFAULT-on-store (#221), signal to parked waiter (#213), child reclaim (#247), traced-thread reap (#280), supervised-stop death wait (#185), yield-broker signal liveness (#275). Pattern: wait/exit/signal state-machine semantics patched reactively, one syscall-interaction corner at a time.
- Pure-testable: YES — the decision core lives in `crates/ginux-process/src/lib.rs` as a fixed-size, syscall-free `ProcessTable<8>` state machine [MEASURED, read of wait()/is_waitable_child()], plus pure selector/status helpers in `ginux-init/src/main.rs`.
- Why coverage is weak: only 19 hand-written `#[test]`s in ginux-process (0.0093 tests/line) vs 8 bug-fix PRs; the init-side half (`resolve_wait_target`, `store_tracee_u32`, `interrupt_parked_waiters`) has ZERO unit tests [MEASURED: `grep -c '#\[test\]' crates/ginux-init/src/*.rs` = 0 for all files]; no property/fuzz target covers wait/signal state (security-fuzzer targets are config/selector/elf/vfs-index/kernel-path/device/syscall/audit — syscall/audit fuzz the contract surface, not the ProcessTable lifecycle) [MEASURED: scripts/fuzz-security.sh target loop].
- Candidate PURE functions (file + fn):
  1. `crates/ginux-process/src/lib.rs` — `ProcessTable::wait` (reportable-child selection + status composition + NotChild/NoExitedChild/ECHILD classification)
  2. `crates/ginux-process/src/lib.rs` — `ProcessTable::is_waitable_child` + `has_waitable_child` (thread-leader rule, wait4 target: Any/Group/Specific)
  3. `crates/ginux-process/src/lib.rs` — `ProcessTable::adopt_orphans` (reparenting on tgid death — fixed by #234)
  4. `crates/ginux-process/src/lib.rs` — `ProcessTable::set_signal_mask` / `next_signal` / `begin_signal` / `signal_return` (sigprocmask+fork+exec state rules — fixed by #191)
  5. `crates/ginux-init/src/main.rs:2354` — `resolve_wait_target` (wait4 selector −1/0/<−1/pid → WaitTarget, pure)
  6. `crates/ginux-init/src/main.rs:2558` — `store_tracee_u32` (page-crossing all-or-nothing put_user emulation; page-split decision is pure, ptrace I/O is a thin seam — fixed by #221)

### 4.2 descriptors / fd-table bookkeeping + /proc/self/fd translation
- Why hot: 4 fixes (#278 console mediation, #288 authoritative descriptor tables, #238 signal-driven I/O refusal, #206 stdio alias write rule) plus adjacent #289/#274 translation fixes; every one is "the virtual fd table disagrees with the real one" — an invariant bug family.
- Pure-testable: YES — the bookkeeping is literal bitmap/table algebra on fixed arrays [MEASURED signatures below].
- Why coverage is weak: ALL of this logic is in `crates/ginux-init/src/main.rs` (12,582 lines) and the whole ginux-init crate has 0 `#[test]` functions in 9 files / ~14.7k lines [MEASURED] — the repo's weakest coverage; only black-box Python scripts (need built binary + C fixture) exercise it; no fuzz/property target for fd algebra.
- Candidate PURE functions (file + fn):
  1. `crates/ginux-init/src/main.rs:4156-4196` — `native_fd_set` / `native_fd_contains` / `native_fd_clear` / `native_fd_assign` / `native_fd_clear_range` (bit-set algebra; direct set/clear/assign↔contains property)
  2. `crates/ginux-init/src/main.rs:4032` — `native_pidfd_reaped` (pidfd table lookup)
  3. `crates/ginux-init/src/main.rs:4088` — `native_pidfd_host_target` (caller+fd → host pid translation, pure table walk)
  4. `crates/ginux-init/src/main.rs:5168` — `native_virtual_proc_fd_number` (/proc/self/fd path → virtual fd; pure string/table logic)
  5. `crates/ginux-init/src/main.rs:12096` — `native_fd_instance_target` (fd translation to instance view, writes into fixed buffer)
  6. `crates/ginux-init/src/launch.rs:757` — `audit_write` + `audit_u64`/`audit_i64` (byte-budget state machine: never split a record, cap at budget — fixed by #187; statics are process-local, testable without VM)

### 4.3 vfs path resolution + image index parsing
- Why hot: 4 fixes (#218 symlink-before-parent ordering, #217 unlink lifetime, #216 failed-open destroys file, #193 GNU sparse misindex) — 3 of them pure single-crate fixes with unit tests; path algebra is the repo's most property-friendly surface (roundtrips, no-panic-on-arbitrary-bytes, resolution determinism).
- Why coverage is weak: 16 hand-written tests in ginux-vfs / 0 in vfs-index beyond a single 20-line release-overflow guard (`crates/ginux-vfs-index/tests/overflow_checks_release.rs`) + shell-level `test-oci-layers.sh`; fuzz target only feeds a 512-byte VFS header seed, not paths/overlay logic [MEASURED: `corpus()` seeds in security-fuzzer/src/main.rs]; no proptest/quickcheck (see §5).
- Candidate PURE functions (file + fn):
  1. `crates/ginux-vfs/src/lib.rs:223` — `resolve_components` (symlink-before-parent resolution order — fixed by #218)
  2. `crates/ginux-vfs/src/lib.rs:119` — `Index::resolve` / `:104` `Index::lookup_exact` (path → entry)
  3. `crates/ginux-vfs/src/lib.rs:132/167/159` — `decode_record` / `encode_record` / `encode_header` (roundtrip + bounds properties)
  4. `crates/ginux-vfs/src/lib.rs:549/542` — `FileSystem::unlink` + `release_unlinked` (unlink-until-last-close lifetime — fixed by #217)
  5. `crates/ginux-vfs-index/src/main.rs:639` — `parse_octal` (tar numeric field parsing, partial/short fields)
  6. `crates/ginux-vfs-index/src/main.rs:619/680` — `normalize_archive_path` + `reject_sparse`/`parse_pax`/`verify_checksum` (malformed-archive no-panic properties — fixed by #193)

Runners-up [INFERRED]: contract/config (8 PRs but mostly planned Gate features, not defects; contract+core libs already carry 27 unit tests), clone (4 PRs, all native-runtime-interaction, hard to make pure without a broker seam).

## 5. Testing-convention findings [MEASURED]

- Property-testing crates: NONE. `grep -rn "proptest|quickcheck" Cargo.toml crates/*/Cargo.toml Cargo.lock` → 0 hits [MEASURED]. No cargo-fuzz/libFuzzer either.
- What exists instead (3 layers):
  1. Rust unit tests: hand-written `#[cfg(test)] mod tests` at the bottom of each lib file. Counts [MEASURED grep of `#[test]`]: ginux-instance 28, ginux-process 19, ginux-vfs 16, ginux-contract 15, ginux-core 12, ginux-runtime 10, ginux-cli 6, ginux-devices 6, ginux-kernel-views 6, ginux-oci 3; **ginux-init crate: 0 across all 9 files (~14.7k lines incl. the 12,582-line main.rs)**. Names are behavior sentences, e.g. `resolves_links_before_parent_components_and_checks_each_directory`, `balanced_contract_refuses_signal_driven_io`.
  2. Bespoke bounded fuzzer: `crates/security-fuzzer` (own xorshift-style `mutate()`, `catch_unwind`, ≤5 s/target via `scripts/fuzz-security.sh`, artifacts to `build/security-fuzz`) over 6 seeds in `tests/fuzz-corpus/{config,selector,elf,vfs-index,kernel-path,device}` and targets config/selector/elf/vfs-index/kernel-path/device/syscall/audit [MEASURED, read of source]. No shrinking, no coverage feedback, corpus of 6 files. Entered main via a direct push (`2b0b020`), not a PR [MEASURED].
  3. Black-box runtime tests: `scripts/test-*.py` (Python, `check(name, cond)` style) + `tests/fixtures/*.c|*.S` C fixtures + `scripts/test-*.sh` + `expect-*.exp` (Tcl expect for systemd logins), all requiring `make build` / image prep [MEASURED: Makefile targets test-unit, test-process-native, test-contract-runtime, test-release-overflow, …].
- Test layout convention [MEASURED]: unit tests inline in `src/lib.rs` under `#[cfg(test)]`; one integration test file in the repo (`crates/ginux-vfs-index/tests/overflow_checks_release.rs`, a `#[should_panic]` release-overflow guard); everything else is `scripts/` + `tests/fixtures/` + `tests/fuzz-corpus/`.
- Implication for C-2/C-3: a property harness would be net-new (add `proptest` as dev-dependency); the natural seams are `ProcessTable<8>` (already syscall-free), the `native_fd_*` bitmap ops and the vfs-index tar parsers (already standalone `fn`s) — ginux-init currently cannot host unit tests without extracting pure helpers from main.rs.

## 6. PRs/day measurement [MEASURED]

UTC-normalized merge dates of the 60 PRs (Python conversion of `%cI`):

| day (UTC) | PR merges |
|----|----|
| 2026-11-05 | 18 |
| 2026-11-06 | 4 |
| 2026-11-07 | 2 |
| 2026-11-09 | 6 |
| 2026-11-13 | 22 |
| 2026-11-14 | 8 (partial, window edge) |

- Window span 8.51 days → **60 PRs ≈ 7.1 PRs/day average**; all-history: 136 PRs / 14.1 days ≈ 9.6 PRs/day.
- The "~20 PRs/day" claim is true only at the burst peak: 22 merges on 2026-11-13 UTC (and 5 merges within 17 minutes on 11-09 15:03–15:20Z) [MEASURED]. Full no-merge days exist inside the window (11-08, 11-10, 11-11, 11-12 UTC) [MEASURED].
- Base SHA at measurement: `285d025b7f8bcad0784585dcfbd23cada4643408` (2026-11-14T05:30:14Z). All counts above are frozen to that head; newer commits (e.g. HEAD's direct push "fix(init): track standard descriptors by backing object") are not counted as PRs.

*All [MEASURED] claims are reproducible with the commands cited in §1 inside `/home/z/my-project/work/upstream-ginux` at the base SHA; per-PR area/defect/pure/test cells are [INFERRED] classifications over those measured inputs.*

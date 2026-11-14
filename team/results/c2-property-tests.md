# C-2 First Piece: Property Tests — ginux-process `ProcessTable<8>`

## 1. Branch + base [MEASURED]

- Branch: `exp/property-tests-process-table` (created from ginux-watch main HEAD `193b8301586b00f7b91dba9e1b5d70315c3610c1`; working-tree only, no commits — supervisor commits).
- Upstream SHA tested: `285d025b7f8bcad0784585dcfbd23cada4643408` (= latest origin/main; re-verified per METHODOLOGY rule 14: `git rev-parse HEAD` + clean `git status` in the upstream clone after the run — untouched).
- New files (all untracked, additive): `property-tests/Cargo.toml`, `property-tests/Cargo.lock` (proptest 1.12.0 pinned), `property-tests/Makefile`, `property-tests/README.md`, `property-tests/tests/process_table_properties.rs` (1566 lines), `property-tests/tests/process_table_properties.proptest-regressions` (2 shrunk seeds, replay green).
- Symlink `upstream -> /home/z/my-project/work/upstream-ginux` created at repo root; already covered by `.gitignore` line 7 (`git check-ignore -v upstream` passes) — no `.gitignore` edit needed, symlink stays untracked.
- Actions dispatch: PENDING — no GitHub token this session; only local runs. Record for the supervisor to dispatch the fuzz/CI workflow after push.

## 2. What was tested [MEASURED]

- Crate: `property-tests/` (`ginux-watch-property-tests`), edition 2021, empty `[workspace]` table, `ginux-process = { path = "../upstream/crates/ginux-process" }` (crate has zero deps, no features), `proptest = "1"` as dev-dependency — same read-only path-dependency + workspace-detach pattern as `fuzz/Cargo.toml`.
- Public API exercised (upstream `crates/ginux-process/src/lib.rs` line refs): `create_init` (273), `fork` (373), `clone_thread` (397), `exec` (411), `exit` (434), `reap_thread` (445), `signaled` (481), `has_waitable_child` (528), `wait` (552), `set_process_group` (593), `set_signal_mask` (667), `signal` (674), `set_signal_action` (686), `signal_action` (700), `next_signal` (708), `begin_signal` (719), `signal_return` (742), `blocking_interrupted` (754), `shutdown` (759), `reap_all` (770), `active` (782), `view` (359), `lookup` (343). Private helpers (`allocate`/`index`/`adopt_orphans`/`is_waitable_child`) are mirrored in the model, not patched.
- 9 proptest properties, 2304 generated cases total (block-level `ProptestConfig::with_cases(256)` at tests/process_table_properties.rs:968 applies to all 9):
  1. `model_matches_process_table_over_random_op_sequences` (256 cases): slot-accurate reference model (transcribed line-by-line from lib.rs) driven by random op sequences (create_init/fork/clone_thread/exec/exit/signaled/reap_thread/wait/has_waitable_child/mask/signal/action/next/begin/return/blocking/set_process_group/shutdown/reap_all over Any/Group/Specific targets incl. wild pids); after EVERY op: view+lookup field equality, `active()`, reaped-pid absence, pid+generation counter monotonicity, exact Ok/Err + payload equality per op (wait slot-order selection and NotChild vs NoExitedChild included).
  2-9 (256 cases each): one-shot reaping with exact statuses; wait returns only dead direct leader children (running parent shields subtree); adoption reparents to init only at last-thread death and preserves waitability (zombie + running orphans, thread-alive holds parent); capacity 8 hard-enforced (zombies occupy slots, fork fails closed, reaping frees exactly one, pids never reused, shutdown+reap_all empties); bad wait/signal targets always typed errors, never panic (validity-before-identity ordering); mask gating + ascending `next_signal` + duplicates collapse + masked-survive-until-clear + SIGKILL/SIGSTOP unblockable; handler-frame lifecycle (auto-mask, nested Default/Ignore still deliver, nested Handler refused with pending preserved, sigreturn restores, double return fails); fork-copies-mask/dispositions-not-pending + exec-resets-caught/keeps-Ignore/pending/mask + epoch monotonic (PR #191 family).

## 3. Run command + results [MEASURED]

```
ln -sfn /home/z/my-project/work/upstream-ginux upstream
PATH=/tmp/cargo/bin:$PATH cargo test --manifest-path property-tests/Cargo.toml
make -f property-tests/Makefile test        # gate-style wrapper, verified
```

- Toolchain: rustc 1.100.0 (0ef1bc386 2026-11-09), cargo 1.100.0, minimal profile installed under `/tmp` only (RUSTUP_HOME=/tmp/rustup CARGO_HOME=/tmp/cargo). Note: `curl https://sh.rustup.rs | sh` pipe stalled >4 min; fallback per directive — direct `rustup-init` download from static.rust-lang.org (3 s) with the same env.
- Result: `9 passed; 0 failed; 0 ignored` — test execution wall 0.51 s; clean build (cold target, warm CARGO_HOME) 9.1 s; compile warnings 0.
- Disk: target dir ~50 MB, 8 GB free — no pressure.

## 4. Failure triage / coverage gap [MEASURED]

- First run: 4 properties failed — ALL were harness bugs, zero upstream failures: (a) wait property reaped a dead child via Specific then expected the Any-drain to return it again (one-shot); (b) mask property expected the post-clear drain to return ALL pending instead of the masked leftovers; (c)+(d) handler-frame and fork properties lacked sig-distinctness assumes (plain_sig collided with handler/ignored sigs). Proptest shrunk each to a minimal seed (kept in `process_table_properties.proptest-regressions`, replay green). No upstream behavior was contradicted at any point.
- Differential model over ~12k random ops (256 cases x <=48 ops, plus replay) found zero divergence at SHA `285d025` → recorded as REGRESSION-COVERAGE ADDITION, not a bug. No memory-safety/isolation-escape/security hint (crate contains zero `unsafe` [MEASURED: rg "unsafe" = 0 hits]).
- Coverage gaps (public-API limits, upstream untouched): no mask/pending getter (observed behaviorally via next_signal/blocking_interrupted); `TaskId` generations not publicly constructible (driver asserts counters against table-returned ids instead); `StaleTask` unreachable via public API pre-wraparound (model mirrors it anyway); `Credentials` mutations, `set_process_group_for`/`create_session`, futex/timer/epoll/PipeSpace types out of this slice.

## 5. Why this region (C-1 cite)

`team/results/c1-hot-surface-map.md` section 4.1: waitid / process reaping + signal delivery is the TOP hot region — 8 fix PRs in 9 days (#234 adoption, #242 SIGCHLD, #221 EFAULT store, #213 parked-waiter signal, #247 child reclaim, #280 traced-thread reap, #185 supervised-stop wait, #275 yield-broker signals), "wait/exit/signal state-machine semantics patched reactively". The decision core is the syscall-free `ProcessTable<8>` with only 19 hand-written tests (0.0093 tests/line) and no property/fuzz target; C-1's candidate pure functions (`wait`, `is_waitable_child`/`has_waitable_child`, `adopt_orphans`, `set_signal_mask`/`next_signal`/`begin_signal`/`signal_return`) are all covered by this harness.

## 6. Next actions

1. Supervisor: commit branch files + dispatch CI (token pending — this session could only run locally [MEASURED]).
2. C-2 second piece: same harness pattern for the ginux-init pure helpers (`resolve_wait_target`, `store_tracee_u32`) flagged in C-1 section 4.1 items 5-6.
3. Optional follow-up: raise model test cases (256 -> 2048) in CI where wall time is cheap, and add a `ReadAction`-style op for `process_group_in_session` if job-control coverage is wanted.

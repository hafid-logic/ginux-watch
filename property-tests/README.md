# C-2 property tests: ginux-process ProcessTable<8>

Purpose: property/model-based regression coverage for the pure wait/reap +
signal-delivery core (`ProcessTable<8>`) of upstream `ginux-process`.

- Upstream SHA tested: `285d025b7f8bcad0784585dcfbd23cada4643408` (read-only
  path dependency, same convention as `fuzz/Cargo.toml`).
- Crate: `property-tests/` (`ginux-watch-property-tests`), tests in
  `tests/process_table_properties.rs`. Upstream code is NOT modified — the
  harness only reads `../upstream/crates/ginux-process`.

## Repro (gate format)

From the repository root:

```sh
ln -sfn <upstream-checkout> upstream
cargo test --manifest-path property-tests/Cargo.toml
```

With the local /tmp toolchain (HANDOFF §1 pattern):

```sh
ln -sfn /home/z/my-project/work/upstream-ginux upstream
PATH=/tmp/cargo/bin:$PATH cargo test --manifest-path property-tests/Cargo.toml
```

Make-style one-liner (creates the symlink if missing; override the upstream
location with `UPSTREAM_CHECKOUT=...` and cargo with `CARGO=...`):

```sh
make -f property-tests/Makefile test
```

CI note: CI checks out upstream at `<repo>/upstream` itself, so there the
`ln -sfn` line is a no-op; `upstream` is gitignored and stays untracked.

## Expected output

```
running 9 tests
test adoption_reparents_children_to_init_and_preserves_waitability ... ok
test bad_wait_and_signal_targets_error_cleanly_without_panicking ... ok
test fork_copies_mask_and_dispositions_not_pending_and_exec_resets_dispositions ... ok
test handler_frames_block_only_handler_delivery_and_restore_mask ... ok
test model_matches_process_table_over_random_op_sequences ... ok
test reaping_is_one_shot_with_exact_statuses ... ok
test signal_mask_gates_delivery_and_never_blocks_kill_stop ... ok
test table_capacity_is_hard_enforced_at_eight ... ok
test wait_returns_only_dead_direct_children_of_the_caller ... ok

test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

(9 proptest properties = 2304 generated cases total: 256 cases per property,
because the block-level `ProptestConfig::with_cases(256)` applies to all nine.)

## What is covered

1. Model-based state machine: a slot-accurate reference model (transcribed
   from upstream `lib.rs` at the SHA above) is driven by random op sequences
   (create_init/fork/clone_thread/exec/exit/signaled/reap_thread/wait/
   has_waitable_child/signal ops/set_process_group/shutdown/reap_all) and
   compared against the real table after every op (view/lookup/active,
   reaped-pid absence, pid+generation counter monotonicity, wait slot-order
   selection, NotChild vs NoExitedChild classification).
2. Invariants: one-shot reaping with exact statuses; wait selects only dead
   direct leader children (running children shield their subtree); orphan
   adoption reparents to init only when the last thread of a group dies and
   preserves waitability; capacity 8 is hard (zombies occupy slots, fork
   fails closed, pids never reused); bogus wait/signal targets always
   return typed errors, never panic; signal mask gating + ascending
   next_signal order + SIGKILL/SIGSTOP unblockable; handler frame lifecycle
   (auto-mask, nested refusal, sigreturn restore); fork-copies-dispositions-
   not-pending and exec-reset rules (PR #191 family).

## Known gaps (public API limits, upstream untouched)

- No public signal-mask or pending-set getter: mask/pending state is only
  observable through `next_signal`/`blocking_interrupted` behavior.
- `TaskId` generations are not publicly constructible, so the harness drives
  the model with table-returned identities and asserts counter drift.
- `Credentials::set_groups/set_uid/set_gid/drop_capabilities` mutations and
  `set_process_group_for`/`create_session` job-control rules are out of
  scope for this C-2 slice (reaping + signal delivery focus); the futex,
  timer, epoll, and PipeSpace types are likewise not covered here.
- `StaleTask` is unreachable through the public API (pids are never reused
  within a table before u32 wraparound); the model mirrors it anyway.

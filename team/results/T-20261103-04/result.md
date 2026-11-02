# T-20261103-04 — Critic review of gap-finder drafts (w5)

Inputs: team/results/T-20261103-{01,02,03}-par/result.md. All [MEASURED] below = commands re-run by w5 in `/home/z/my-project/work/ginux` (read-only, main=95f8ef24) unless another path is cited. Snapshot: /home/z/my-project/work/data-wt (2026-11-02T22:05:39Z, 56 items).

## Method

Re-ran per draft: diff/numstat/merge-base/SHA verification plus at least one 0-hit grep, and the three card-flagged strong claims (§verdicts). Duplication scan of upstream-dump.jsonl via python3 (keywords `regression`, `getcwd`, per-item files/state).

## Draft T-20261103-01-par (PR #37 gap)

Verified [MEASURED]: `git diff --stat 759cf2e2 eac4a784` = 2 files (gate doc +81, address_space.rs); merge-base=759cf2e2; commit b79cdb8a date/Signed-off-by match; `git diff eac4a784 origin/main -- kernel/src/address_space.rs` empty; hunks match quoted code (short-circuit removal; `if valid && owned_released`); `run_linux_init` at line 249; caller lib.rs:4226 `Failed` path has no frame release → leak inference sound [INFERRED]; greps `owned_released`/`setup failed at stage` in tests/,tools/ = 0 hits; Makefile `test:`→boot.sh and clippy ginux-kernel at Makefile:277 confirmed.

1. §1 "kernel/src/address_space.rs (+5/−3)" — wrong. `git diff --numstat 759cf2e2 eac4a784` = `2 3 kernel/src/address_space.rs` [MEASURED]. Fix: "+2/−3" (the "5" was the --stat total).
2. §1 "so the six … frames … leaked on every failed … attempt" is untagged; tag [INFERRED] (correct given lib.rs:4226, but it is an inference).
Strong claim "reintroducing the bug passes make check/test": draft does not assert it as measured — §3 greps + §5 [INFERRED] hedge are accurate [MEASURED greps]. APPROVED except items 1–2.

**Verdict: REVISE (items 1, 2 — numeric only; content sound).**

## Draft T-20261103-02-par (PR #38 gap)

Strong claim VERIFIED [MEASURED]: `git diff 759cf2e2 pr-38 -- kernel/` = single line, cpu.rs:22907 `PATH_CAPACITY + 1` → `+ 2`; PATH_CAPACITY=256 at linux_overlay.rs:9; copy_path (linux_overlay.rs:465) uses `get_mut(..len)` so a 256-byte path fills `output[1..]` exactly; then length=257, required=258, `&output[..required]` on the old 257-byte array panics. Math recomputed and correct. Greps getcwd/erange/PATH_CAPACITY in tests/ = 0 hits; published_rootfs.rs:240 sentinel confirmed; dump item #21 open, `files: []`.

1. §1 line numbers off by 3: `required = length + 1` is cpu.rs:22940 (not 22937); the slice is cpu.rs:22944 (not 22941); ERANGE block 22941–22943 (not 22938–22940); EFAULT return at 22945. `copy_to_linux_user` impl 38956–38963 and fn start 22905 are correct [MEASURED via grep -n]. Fix: update the four refs.
2. §4 "PR 54 … would turn the pre-fix out-of-bounds slice into a deterministic panic in release builds" — wrong mechanism: slice-range panics are independent of `overflow-checks` and already fire in release; PR #54 is adjacent only by file/keyword [INFERRED from PR #54 scope in STATE.md/matrix P10]. Fix: reword to "adjacent by file only; does not change this panic behavior".

**Verdict: REVISE (items 1, 2).**

## Draft T-20261103-03-par (PR #41 gap)

Strong claim VERIFIED [MEASURED]: `git show 078b63b9:.github/workflows/issue-14-linux-repro.yml` → trigger literally `branches: dae/issue-14-native-volume-linux]` (scalar with stray `]`, no list, no `main`), same file on origin/main → pushes to main never trigger it. Merge 1203e291 parents fbe6472e+078b63b9 confirmed; `merge-base pr-41 origin/main`=078b63b9; pci.rs symbols at 993/1072/1113/3768/3788; no `cfg(test)` in pci.rs; boot.sh artifact mkdir/copies at @078b63b9 lines 11–12/41–47; diffstat 7 files +284/−19. Nuance (non-blocking): a scalar string is schema-valid for GH Actions `branches:`; the defect is the stray `]` + branch-only scope — draft already tags the consequence [INFERRED]; optional clarifying word. No overstatement found; §5 properly [UNVERIFIED].

**Verdict: APPROVE.**

## Cross-cutting

- Duplication: python3 scan of upstream-dump.jsonl → 0 items contain "regression"; `getcwd` only #38/#21; none of the three proposed test gaps appears in the snapshot or in our published #4, #14, #43, PR #54 comment 6574390843 (different topics: QEMU queue size, env data point, overflow-checks config, five eager underflow sites) [MEASURED, scan + STATE.md].
- Secrets: none found in any draft (public SHAs/run IDs only) [OBSERVED].
- Language: internal English OK; no upstream-bound text produced [OBSERVED].
- Ranking: all three strong claims verified mechanically; #38 evidence is the tightest (exact one-line diff + recomputed panic math), #37 verified but its test needs a new serial marker + scenario, #41 coverage is race-dependent [INFERRED]. Consistent with supervisor best-two #37+#38.

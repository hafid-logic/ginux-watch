# T-20261103-07 — oci fuzz target packaging — result (worker-oci)

Status: **done**. One commit on `card/oci` in the fork worktree, bookkeeping committed and pushed to `hafid-logic/ginux-watch`.

## Deliverable

Commit `1da0fd93` ("fuzz: oci_surfaces harness + seeds (53) + oci.dict") on branch `card/oci` of worktree `/home/z/my-project/work/wt-fuzz-oci` (parent `47055afb` = `feature/fuzz-targets` scaffolding). Adds exactly three path groups:

- `fuzz/fuzz_targets/oci_surfaces.rs` (164 lines, 8 OCI surfaces)
- `fuzz/corpus-seed/**` (53 seed files)
- `fuzz/oci.dict` (58 lines, 1600 bytes)

## [MEASURED] isolation

`git -C /home/z/my-project/work/wt-fuzz-oci diff --stat feature/fuzz-targets..card/oci` → "55 files changed, 244 insertions(+)", listing only `fuzz/corpus-seed/*` (53), `fuzz/fuzz_targets/oci_surfaces.rs`, `fuzz/oci.dict`. A name-only filter excluding those three path groups returned 0 paths. Evidence: `evidence/diff-stat-isolation.txt`, commit SHA `1da0fd93`.

## [MEASURED] seed corpus verification

- Seed file count: 53 in source (`ginux-watch/fuzz/corpus-seed/`), 53 in worktree copy — matches the card's required 53.
- Empty files: 0.
- Byte identity: `cmp` over all 53 files source→worktree: 0 mismatches.
- Total size: 70,650 bytes; `fuzz/oci.dict` 1600 bytes, `cmp`-identical to source.
- Largest file: `t30_multi` 4,608 bytes; next `t06_pax_chain` 3,584; `t17_replacement` 3,072.
- Spot-check (3 tar seeds, `t01_file`, `t06_pax_chain`, `t30_multi`): `file` reports "POSIX tar archive"; byte 257 = `75 73 74 61 72 00 30 30` (`ustar\0` + version `00`) — valid tar magic (`xxd` unavailable in sandbox, `od -t x1z` used).

Evidence: `evidence/measurements.txt`, worktree path `fuzz/corpus-seed/`.

## Header-comment edits (comments only, no code logic)

1. Path-dependency reference `../upstream/crates/oci` → `../crates/oci` (line 6).
2. Kernel citation `kernel/src/published_rootfs.rs@82df3d71` → `@c86945b1` (line 12), same wording otherwise.

`diff` of source vs worktree copy shows exactly those 2 changed lines, both comment lines.

Citation update justification [MEASURED]: at `c86945b1`, `git -C /home/z/my-project/work/fork grep -c "<fn>" c86945b1 -- kernel/src/published_rootfs.rs` returns `entry_and_next_at_offset`=1, `find_index`=7, `next_child`=1, `copy_path`=1, and `cat-file -t c86945b1:kernel/src/published_rootfs.rs` = blob. File+functions still exist at `c86945b1`, so the citation SHA was updated per the card. The inline reference "(entry_and_next_at_offset, line 207)" in a code comment was left untouched (comment-only rule: line number may differ at c86945b1; flagged for follow-up below).

## [OBSERVED] anomalies / notes

- Shared clone `ginux-watch` was concurrently used by `worker-rules` (uncommitted edit to `team/tasks/claimed/T-20261103-06.md` present in the working tree). Plain `git pull --rebase` aborted (exit 128, dirty index); run as `git -c rebase.autoStash=true pull --rebase` → "Already up to date" (0 behind / 0 ahead after fetch), other worker's dirty state preserved. Claim commit `d903e2a` was pathspec-scoped to my card file only.
- All copied files (seeds, dict, harness) carry mode 755 because the read-only inputs in `ginux-watch/fuzz/` are 755; modes faithfully mirror the source, not introduced by this task.
- Claim was pushed before work started per PROTOCOL §Claiming; card moved to `done/` after delivery.

## [UNVERIFIED]

- Compilation of the harness (and coverage yield) — not run locally per rules ("never run cargo build"); GitHub Actions `fuzz` workflow will verify. The harness references `ginux_oci` APIs that the scaffolding's path dependency `../crates/oci` must export; not compiled here.

No secrets, no placeholders, no pushes to `gmkurtzer/ginux`.

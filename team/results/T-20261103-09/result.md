# T-20261103-09 — volume fuzz target packaging (worker-volume)

## Status: done

Deliverable commit on `card/volume`: **2c1a3aa1** ("fuzz: volume_surfaces harness
+ seeds (26) + volume.dict"), parent 47055afb (feature/fuzz-targets head), in
worktree `/home/z/my-project/work/wt-fuzz-vol`.

## Claims

- [MEASURED] Commit 2c1a3aa1 touches ONLY the three assigned path groups:
  `git -C /home/z/my-project/work/wt-fuzz-vol diff --stat feature/fuzz-targets..card/volume`
  → 28 files changed, 67 insertions; 26 × `fuzz/corpus-seed-volume/*.bin`,
  `fuzz/fuzz_targets/volume_surfaces.rs` (57 lines), `fuzz/volume.dict` (9 lines).
  No other path appears (28 = 26 + 2). Evidence: commit 2c1a3aa1 diff.

- [MEASURED] Seed corpus: exactly 26 files, 0 empty, total 10063 bytes.
  Size distribution: 19 × 512 B, 6 × 48 B, 1 × 47 B. Largest = 512 B (19 files,
  one sector each; e.g. `26-record-payload-host-header.bin`,
  `17-junk-sector.bin`, `18-committed-gen1-len255.bin`); smallest = 47 B
  (`24-host-header-short-47.bin`). Evidence: worktree path
  `fuzz/corpus-seed-volume/` at commit 2c1a3aa1 (find -type f -printf '%s').

- [MEASURED] Copies are byte-identical to the read-only sources:
  `diff -rq ginux-watch/fuzz/corpus-seed-volume wt-fuzz-vol/fuzz/corpus-seed-volume`
  → no differences; `cmp` on `fuzz/volume.dict` → identical. Harness sha256
  03a2623a8fa1e4f619309c38703cc228ec38a83c2ae4c4445d5704bc2fbd1708; dict sha256
  88be25d2b8115aa55767554186834d97b04fe5e1fe565024dadf19fd8a8ef4b3.

- [MEASURED] Comment-only adaptation, no code-logic change: `diff` of the
  committed harness vs `ginux-watch/fuzz/fuzz_targets/volume_surfaces.rs` shows
  exactly 3 changed lines, all comments (`//!` lines 1 and 5, `//` line 32).

- [MEASURED] Kernel-chain citation verified and updated to c86945b1:
  `git -C /home/z/my-project/work/fork grep -n "Record::decode\|HostVolumeHeader::decode" c86945b1 -- kernel/src/lib.rs`
  → exit 0, matches at kernel/src/lib.rs:1317
  (`|| ginux_volume_format::HostVolumeHeader::decode(verified.payload())`) and
  :1332 (`&& ginux_volume_format::HostVolumeHeader::decode(verified.payload())`).
  Line numbers 1317/1332 are unchanged vs 82df3d71 (same grep at 82df3d71
  returns identical lines/numbers); only the SHA was updated, in both citation
  comments (harness lines 5 and 32, now `kernel/src/lib.rs:1317/1332@c86945b1`).

- [INFERRED] `../crates/volume-format` in the harness doc comment matches the
  actual in-repo path dependency `fuzz/Cargo.toml`
  (`ginux-volume-format = { path = "../crates/volume-format" }`, present at
  47055afb), and `crates/volume-format` exists on card/volume.

- [UNVERIFIED] Harness compile/run behavior: cargo build/check/fuzz runs are
  forbidden for workers (protocol); validation happens in GitHub Actions. The
  committed harness is byte-identical to the reviewed source except the three
  comment lines above.

## Anomalies / notes

1. No literal `../upstream/` reference existed in the source harness: line 1
   already said `crates/volume-format`. Normalized (comment-only) to
   `../crates/volume-format` per the card's path-dependency rule, matching
   fuzz/Cargo.toml.
2. The card's grep pattern matched only `HostVolumeHeader::decode`;
   `Record::decode` has no literal occurrence in kernel/src/lib.rs at c86945b1
   (record decoding happens inside `volume::recover`). Grep exit 0 → treated
   as "found" per the card.
3. The inline citation (line 32) previously lacked a SHA; `@c86945b1` added for
   consistency with the doc comment (comment-only).
4. Shared checkout `/home/z/my-project/ginux-watch` held another worker's
   uncommitted changes (`M team/tasks/claimed/T-20261103-06.md`, untracked
   `team/results/T-20261103-07/`), which blocked `git pull --rebase` there.
   Bookkeeping was done in an isolated clone
   `/home/z/my-project/work/gw-vol-bookkeeping` to avoid touching their state;
   the shared checkout was left untouched. No upstream (gmkurtzer/ginux) push.
5. Budget: card budget_min 20; measured duration ~5 min (see meta.json).

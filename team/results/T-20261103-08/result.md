# T-20261103-08 — Protocol fuzz target packaging (worker-protocol)

Deliverable shipped on branch `card/protocol` in worktree `/home/z/my-project/work/wt-fuzz-proto`: commit **7991a4f597f2b2235d088978b9193dd19059c554** ("fuzz: protocol_surfaces harness + seeds (34) + protocol.dict"), parent `47055afb` (= feature/fuzz-targets, as specified on the card). No push to upstream gmkurtzer/ginux; no cargo build/check run; only the three authorized path groups touched.

## What was done

1. Copied `ginux-watch/fuzz/fuzz_targets/protocol_surfaces.rs` → `wt-fuzz-proto/fuzz/fuzz_targets/protocol_surfaces.rs` [MEASURED, evidence/seed-stats.txt]: sha256 identical on both sides (`e47d8cd6…41e6ad`).
2. Comment adaptation `../upstream/...` → `../crates/...` [OBSERVED, evidence/seed-stats.txt]: grep of the source harness found **0 occurrences** of `../upstream/` (the only "upstream" match is prose on line 70, "upstream test does_not_mutate_rejected_echo_request", not a path). Line 3 already names `crates/protocol-state`, and the committed `fuzz/Cargo.toml` (from T-20261103-10) already uses `path = "../crates/protocol-state"` (line 17). Therefore **no comment edit was needed; the copy is byte-identical**. [INFERRED: the `../upstream/` reference the card anticipated was already normalized in the source draft.]
3. Copied `fuzz/corpus-seed-protocol/` (34 files) and `fuzz/protocol.dict` into the worktree [MEASURED, evidence/seed-stats.txt]: `diff -r` reports the directories identical; `protocol.dict` sha256 identical (`2a19ace2…1db48`), 637 bytes, 23 lines.
4. Committed with the card identity flags; verified isolation [MEASURED, evidence/diff-stat.txt]: `git diff --stat feature/fuzz-targets..card/protocol` = 36 files, 97 insertions, 0 deletions — exactly `fuzz/fuzz_targets/protocol_surfaces.rs` (74 lines), `fuzz/corpus-seed-protocol/**` (34 files), `fuzz/protocol.dict` (23 lines). Nothing outside the three path groups.

## Seed corpus [MEASURED] (evidence/seed-stats.txt)

- File count: **34** (card requirement: exactly 34 — met).
- Empty files: **0**.
- Total bytes: **3110**.
- Largest file: `p22_ipv4_maxish` = **1442 bytes** (smallest, for reference: `p30_icmp_short7` = 7 bytes).

## API verification — every ginux_protocol_state symbol the harness uses vs c86945b1 [MEASURED]

Method: for each name, `git -C /home/z/my-project/work/fork grep -n "<name>" c86945b1 -- crates/protocol-state/src/lib.rs`; raw outputs in evidence/api-grep.txt.

| Symbol (kind) | Exists at c86945b1 | grep evidence (lib.rs line) |
|---|---|---|
| `parse_arp_reply_v4` (pub fn) | YES | :27 |
| `parse_ipv4_icmp_v0` (pub fn) | YES | :85 |
| `parse_icmp_echo_request_v0` (pub fn) | YES | :147 |
| `build_icmp_echo_reply_v0` (pub fn) | YES | :164 |
| `NeighborStateV4::new` (pub const fn) | YES | :219 |
| `NeighborStateV4::observe` (pub fn) | YES | :227 |
| `NeighborStateV4::mac` (pub const fn) | YES | :248 |
| `NeighborStateV4::accepted` (pub const fn) | YES | :252 |
| `EndpointV4` (pub struct) | YES | :7 (pub fields `mac`, `ipv4` :8–9) |
| `NeighborStateV4` (pub struct) | YES | :212 |
| `Ipv4PacketV0` (pub struct) | YES | :68 (pub fields `source_ipv4`, `destination_ipv4`, `protocol`, `payload`) |
| `IcmpEchoRequestV0` (pub struct) | YES | :128 (pub fields `identifier`, `sequence`, `payload`) |

**Result: 12/12 symbols present; zero drift, zero renames. No code or comment changes were required beyond the copy, so no `blocked_on_api_drift` condition applies.**

## Compliance [OBSERVED]

- Only `fuzz/fuzz_targets/protocol_surfaces.rs`, `fuzz/corpus-seed-protocol/**`, `fuzz/protocol.dict` modified in the worktree (evidence/diff-stat.txt).
- ginux-watch `fuzz/` sources used read-only; no mutation (checksums match before/after copy).
- No cargo build/check/test executed; no secrets; no placeholders; no upstream pushes.
- No code logic changed: `git diff` shows the harness as a pure addition (74 new lines, 0 modified lines elsewhere) [MEASURED, evidence/diff-stat.txt].

## Bookkeeping

- Claimed: commit `6802c36` "claim T-20261103-08 by worker-protocol" (card → team/tasks/claimed/, status: claimed, claim_until 2026-11-03T07:59:34Z), pushed to hafid-logic/ginux-watch main [MEASURED].
- Shared checkout note: `git pull --rebase` initially refused due to another worker's unstaged edit (`team/tasks/claimed/T-20261103-06.md`); ran `git pull --rebase --autostash` — "Already up to date" (HEAD == origin/main, 0 commits behind after fetch), and the foreign edit was restored untouched [OBSERVED].
- Not executed (not available in this environment, stays [UNVERIFIED]): compiling the harness and running libFuzzer on the 34 seeds — that belongs to the Actions `fuzz` workflow per team/PROTOCOL.md §Environment.

## Artifacts

- `card/protocol` @ `7991a4f5` (worktree /home/z/my-project/work/wt-fuzz-proto).
- evidence/api-grep.txt — full grep outputs for the table above.
- evidence/seed-stats.txt — checksums, corpus identity, seed measurements.
- evidence/diff-stat.txt — isolation diff --stat and touched-path list.

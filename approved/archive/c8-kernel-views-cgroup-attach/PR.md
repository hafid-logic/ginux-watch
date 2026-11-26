### What
Pins `CgroupFs::attach`: pid 0 and non-root actors are rejected; attaching a pid already in another group moves it (single membership); a group at its `pids.max` rejects a new distinct pid with `LimitExceeded`.

### Why it matters
Attach enforces single membership across groups and the per-group pid cap. The existing tests attach one pid to one group, so dropping the cross-group removal loop or the `pids.max` guard survives the suite while breaking isolation accounting.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| skip cross-group removal loop | PASS (survives) | FAIL (killed) |
| drop `member_count >= pids_max` guard | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib attach_moves`.

Prepared with AI assistance; reviewed by me.

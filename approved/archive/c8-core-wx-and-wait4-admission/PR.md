### What
Sweeps every `prot` combination 0..8 for `mmap` (9) and `mprotect` (10): admission holds iff the bits do not request WRITE and EXEC together, including higher prot bits. Also pins `wait4` pid admission: pid 0 is rejected while `-1` and positive pids are admitted.

### Why it matters
W^X is an isolation invariant of the balanced contract, and `wait4` pid 0 would target a process group the single-task contract does not model. Neither arm had a direct test, so relaxing either passes the existing suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| narrow the W^X mask to `PROT_EXEC` only | PASS (survives) | FAIL (killed) |
| drop the `wait4` pid check | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib mmap_mprotect_reject`.

Prepared with AI assistance; reviewed by me.

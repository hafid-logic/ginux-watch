### What
Pins `/proc/<pid>/stat` rendering: pid 1 is labelled `(init)`, other tasks `(managed)`, and a running task reports state `R`.

### Why it matters
Userspace tooling parses the stat label and state character. The existing suite reads status/identity leaves but never stat, so swapping the init predicate or the state mapping passes it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| init predicate `pid == 1` -> `pid == 2` | PASS (survives) | FAIL (killed) |
| `Running => 'R'` -> `'Z'` | PASS (survives) | FAIL (killed) |

Spec-Ref: proc(5) /proc/[pid]/stat fields (comm, state).

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib procfs_stat_labels`.

Prepared with AI assistance; reviewed by me.


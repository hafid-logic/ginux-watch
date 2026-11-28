### What
Pins `ProcessTable::exec_group`: the calling thread replaces its thread-group leader, returns the leader id with a bumped exec epoch, and leaves tasks outside the group untouched.

### Why it matters
Linux `execve` from a non-leader thread tears down only threads sharing that tgid. Weakening the leader lookup (`occupied && pid == tgid` -> `||` or `!=`) or the teardown filter would either fail every group exec or wipe unrelated tasks. No existing test calls `exec_group`, so all four mutations survive the current suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| leader lookup `&&` -> `\|\|` | PASS (survives) | FAIL (killed) |
| leader lookup `==` -> `!=` | PASS (survives) | FAIL (killed) |
| teardown filter `&&` -> `\|\|` | PASS (survives) | FAIL (killed) |
| teardown filter `==` -> `!=` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib exec_group_replaces_leader`.

Spec-Ref: execve(2) thread-group semantics (leader replacement, same-tgid teardown)

Prepared with AI assistance; reviewed by me.
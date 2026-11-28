### What
Pins `parse_controllers`: OR-accumulation of cpu/memory/pids flags, empty-token skipping for trailing/double spaces, unknown-token rejection, and empty-input zero result.

### Why it matters
Controller parsing gates cgroup subtree delegation; replacing `|=` with `&=` drops previously parsed controllers on multi-token input, and deleting the empty-token arm turns benign whitespace into a permission error. No existing test exercises this function.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `|=` -> `&=` | PASS (survives) | FAIL (killed) |
| delete `b"" => continue` arm | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-kernel-views --lib parse_controllers_accumulates`.

Spec-Ref: cgroup v2 subtree_control documentation

Prepared with AI assistance; reviewed by me.

### What
Pins `remove` busy semantics: an active child group blocks parent removal, leaf groups remove cleanly, freed inactive slots never block, root and non-root callers are denied.

### Why it matters
The busy guard chains `active && path != self && parent == path`; flipping any operator lets parents of live children be removed (orphaning confinement) or blocks legitimate cleanup. Existing tests pin only the member-count branch.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `group.active &&` -> `group.active ||` | PASS (survives) | FAIL (killed) |
| `parent_path(...) == path` -> `!= path` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-kernel-views --lib remove_busy_only`.

Prepared with AI assistance; reviewed by me.

### What
Pins `balanced_surface`: syscall 318 (getrandom) maps to `Random`, `exit`/`exit_group` map to `Lifecycle`, and the console/memory/denied mappings hold.

### Why it matters
The surface table drives the balanced contract's decision. The existing tests check image-read/memory/task arms but not the random or lifecycle arms, so deleting either survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `318 => Random` arm | PASS (survives) | FAIL (killed) |
| delete `SYS_EXIT \| SYS_EXIT_GROUP => Lifecycle` arm | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib balanced_surface`.

Prepared with AI assistance; reviewed by me.

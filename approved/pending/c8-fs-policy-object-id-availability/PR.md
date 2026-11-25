### What
Pins `ObjectId::is_available`: an object is available iff `device != 0` OR `inode != 0`. The test covers `(0,0)` unavailable and `(7,0)`, `(0,7)`, `(7,9)` available.

### Why it matters
Availability gates object identity. The existing tests do not exercise `is_available` directly, so a fault that requires both components nonzero (or inverts the device check) survives them.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `device != 0` -> `== 0` | PASS (survives) | FAIL (killed) |
| `||` -> `&&` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-fs-policy --lib object_id`.

Prepared with AI assistance; reviewed by me.

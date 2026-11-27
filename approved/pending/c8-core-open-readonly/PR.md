### What
Pins open(2)/openat(257) admission to read-only: any write access mode or mutating flag is denied.

### Why it matters
The balanced surface is read-only for opens; widening it would admit writes. Existing tests pin writev/wait4 but not open flags.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop O_ACCMODE from open mask | PASS (survives) | FAIL (killed) |
| openat mask -> 0 | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-core --lib open_admission_is_readonly`.

Prepared with AI assistance; reviewed by me.

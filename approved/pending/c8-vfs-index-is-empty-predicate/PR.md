### What
Pins `Index::is_empty` against exact record counts: a zero-record index reports len 0 and is_empty true, while one-record and multi-record indexes report their exact len and is_empty false.

### Why it matters
Callers use the emptiness predicate before sizing iteration over the index. Inverting the comparison (`count != 0`) or constant-folding it to `true` misreports every non-empty index as empty (or vice versa), silently skipping base-image entries. No existing test builds an empty index or asserts the predicate.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `count == 0` -> `count != 0` | PASS (survives) | FAIL (killed) |
| `is_empty -> true` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-vfs --lib index_is_empty_predicate`.

Spec-Ref: VFS index contract (emptiness predicate vs record count)

Prepared with AI assistance; reviewed by me.
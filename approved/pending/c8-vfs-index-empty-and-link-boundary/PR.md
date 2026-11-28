### What
Pins two VFS index guards: `Index::is_empty` reports true only for a zero-record index, and `Index::resolve` accepts a symlink whose target length equals the link buffer (`MAX_LINK`) exactly — the copy gate is `>` not `>=`.

### Why it matters
An inverted or constant-folded `is_empty` misreports index state to callers sizing iteration. Relaxing the link-length gate to `>=` rejects valid exact-fit targets. Existing tests never build an empty index nor an exact-MAX_LINK link.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `count == 0` -> `count != 0` (is_empty) | PASS (survives) | FAIL (killed) |
| `is_empty -> true` | PASS (survives) | FAIL (killed) |
| link-length gate `>` -> `>=` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-vfs --lib index_is_empty_and_resolve_link`.

Spec-Ref: VFS index contract (emptiness predicate; symlink target buffer bound)

Prepared with AI assistance; reviewed by me.
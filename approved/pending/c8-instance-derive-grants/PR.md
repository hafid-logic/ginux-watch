### What
Pins that a create-only filesystem list still derives the filesystem.** write grant.

### Why it matters
Write authority must follow create capability; dropping the create clause under-grants. Existing tests don't pin this derivation.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop filesystem_create clause | PASS (survives) | FAIL (killed) |
| && -> || in write condition | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib derive_grants_write_from_create`.

Prepared with AI assistance; reviewed by me.

### What
Pins `derive_contract_grants`: a create-only filesystem policy derives the `filesystem.**` write grant while read stays ungranted.

### Why it matters
Create implies mutation; dropping the create arm or requiring both lists silently unmediates creation paths. Existing recipes always set read+write+create together, so the create-only edge is unpinned.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop `|| !filesystem_create...is_empty()` | PASS (survives) | FAIL (killed) |
| `||` -> `&&` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib create_only_filesystem_grants`.

Prepared with AI assistance; reviewed by me.

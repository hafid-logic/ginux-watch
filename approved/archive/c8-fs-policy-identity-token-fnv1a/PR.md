### What
Pins `identity_token` to exact FNV-1a reference hashes for empty, rocky, and peer inputs.

### Why it matters
Instance identity tokens gate capability separation; changing the XOR accumulation to AND/OR produces different hashes that still pass stability/separation checks but break cross-component identity agreement. Existing tests verify properties, not exact values.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `^=` -> `&=` | PASS (survives) | FAIL (killed) |
| `^=` -> `|=` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-fs-policy --lib identity_token_matches_fnv1a`.

Spec-Ref: FNV-1a hash specification (offset basis 0xcbf29ce484222325, prime 0x100000001b3)

Prepared with AI assistance; reviewed by me.

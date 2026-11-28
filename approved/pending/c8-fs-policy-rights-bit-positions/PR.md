### What
Pins every `Rights` constant to its exact bit position (LOOKUP=1<<0 … EXECUTE=1<<5) and asserts pairwise non-containment so no two rights collapse onto the same bit.

### Why it matters
Capability checks are bitwise: shifting a constant right (`1 >> 3 == 0`) turns CREATE into the empty right that authorizes nothing, while colliding bits silently grant extra permissions. The existing `rights_contains_requires_every_requested_bit` test is shift-invariant (it only checks containment algebra), so it survives every `<<`->`>>` mutation.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `CREATE: 1 << 3` -> `1 >> 3` | PASS (survives) | FAIL (killed) |
| `METADATA: 1 << 4` -> `1 >> 4` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-fs-policy --lib rights_constants_pin_exact`.

Spec-Ref: capability rights bitmask contract (distinct single-bit rights)

Prepared with AI assistance; reviewed by me.
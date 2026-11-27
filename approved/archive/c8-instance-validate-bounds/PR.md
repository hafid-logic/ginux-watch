### What
Pins `validate` resource bounds: vcpus 1..=64, memory 16..=1048576; out-of-range rejected, boundary accepted.

### Why it matters
Bounds are fail-closed config gates; widening them admits invalid configs. Existing tests don't pin the exact edges.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `1..=64` -> `1..=65` | PASS (survives) | FAIL (killed) |
| `16..=` -> `15..=` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib validate_enforces_vcpu`.

Prepared with AI assistance; reviewed by me.

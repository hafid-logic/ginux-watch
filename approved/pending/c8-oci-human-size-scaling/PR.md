### What
Pins `human_size` unit scaling: bytes below 1024 stay B, exact powers render KiB/MiB/GiB with one decimal, and values beyond GiB cap at the largest unit.

### Why it matters
Progress reporting relies on correct magnitude; flipping the loop threshold or stalling the unit counter renders every size as bytes. No existing test exercises human_size directly.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `>= 1024.0` -> `< 1024.0` | PASS (survives) | FAIL (killed) |
| `unit += 1` -> `unit *= 1` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-oci --lib human_size_scales`.

Spec-Ref: IEC 80000-13 binary prefixes (KiB/MiB/GiB)

Prepared with AI assistance; reviewed by me.

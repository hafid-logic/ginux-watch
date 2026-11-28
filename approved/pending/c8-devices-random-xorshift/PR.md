### What
Pins `DeviceRegistry::read` Random xorshift64 sequence: first four bytes match the reference algorithm from default seed, and successive reads advance state.

### Why it matters
The PRNG drives /dev/random output; replacing XOR with OR or flipping shift direction produces a degenerate or predictable stream. Existing tests verify read succeeds but never pin output values.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `^= ... << 13` -> `\|= ... << 13` | PASS (survives) | FAIL (killed) |
| `<< 13` -> `>> 13` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-devices --lib random_read_pins`.

Spec-Ref: xorshift64 PRNG (Marsaglia 2003), /dev/random semantics

Prepared with AI assistance; reviewed by me.

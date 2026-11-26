### What
Pins `DeviceRegistry::read` for pseudo devices: two registries with the same initial state produce an identical Random stream, successive reads advance the state (never a constant fill), Zero fills the buffer exactly, and both report the full requested length.

### Why it matters
The existing suite checks that Random output is non-zero but never that it advances per read or that the returned length matches the buffer. A constant fill or a zero length return passes it while silently breaking userspace read loops.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| Random byte becomes a constant `0x42` | PASS (survives) | FAIL (killed) |
| Random returns `Ok(0)` instead of `output.len()` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib random_reads_are`.

Prepared with AI assistance; reviewed by me.

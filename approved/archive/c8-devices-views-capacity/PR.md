### What
Pins `DeviceRegistry::views` truncation: with more assigned devices than output slots, exactly the first `output.len()` views are projected in assignment order and the returned count is capped; a zero-length output projects nothing.

### Why it matters
The projection writes into a caller-fixed buffer. The existing test uses an output larger than the assignment set, so removing or weakening the capacity break survives the suite — and would index past the buffer.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| remove `count == output.len()` break | PASS (survives) | FAIL (killed) |
| `count == output.len()` -> `count > output.len()` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib views_truncate`.

Prepared with AI assistance; reviewed by me.

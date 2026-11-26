### What
Pins `DeviceRegistry::views`: pseudo devices project their fixed major/minor (Zero = 1,5; Random = 1,8), only the requesting instance's devices are returned, the output cap limits the count, and an untouched tail / empty output behave correctly.

### Why it matters
The view projection feeds userspace device metadata. The existing test checks names/kinds but not the numeric major/minor nor the output cap, so a wrong minor or a removed cap survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `Zero => (1, 5)` -> `(1, 3)` | PASS (survives) | FAIL (killed) |
| remove `count == output.len()` cap | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib views_pin_major`.

Prepared with AI assistance; reviewed by me.

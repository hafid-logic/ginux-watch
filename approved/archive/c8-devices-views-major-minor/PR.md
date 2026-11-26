### What
Pins `DeviceRegistry::views` numeric device identity: Zero projects major/minor (1, 5) and Random projects (1, 8), alongside instance filtering and the untouched output tail.

### Why it matters
The merged truncation test pins counts and names but not the numeric major/minor pairs. Userspace mounts devtmpfs nodes from these numbers; a wrong minor silently maps the wrong device while passing the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `Zero => (1, 5)` -> `(1, 3)` | PASS (survives) | FAIL (killed) |
| `Random => (1, 8)` -> `(1, 9)` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib views_pin_major`.

Prepared with AI assistance; reviewed by me.

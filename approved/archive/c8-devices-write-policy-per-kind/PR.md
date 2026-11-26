### What
Pins `DeviceRegistry::write` per device kind: `null` swallows the payload and reports its full length (including a zero-length write returning `Ok(0)`), while `zero` and `random` are read-only and return `PermissionDenied`. A foreign instance cannot reach the descriptor.

### Why it matters
Write accounting is what userspace `write(2)` returns. The existing suite covers random reads and block policies but never a zero-length write to `null` nor writes to `random`, so short-reporting or admitting a read-only kind passes it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| admit `Random` writes as `Ok(len)` | PASS (survives) | FAIL (killed) |
| reject empty `null` writes | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib device_write_policy`.

Prepared with AI assistance; reviewed by me.

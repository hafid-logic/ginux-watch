### What
Pins `validate` identifier rules for both id and hostname: empty/spaced rejected, dotted alnum accepted, hostname checked independently.

### Why it matters
Hostname defaults to id, so suites that never set a distinct hostname cannot detect a skipped hostname check. Removing either validation call survives today.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| skip `validate_identifier(self.id...)` | PASS (survives) | FAIL (killed) |
| skip `validate_identifier(self.hostname...)` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib validate_pins_identifier`.

Prepared with AI assistance; reviewed by me.

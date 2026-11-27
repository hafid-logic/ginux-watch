### What
Pins validate_identifier via validate: empty or space-containing ids rejected, valid id accepted.

### Why it matters
Identifier validation is a fail-closed gate; weakening it admits malformed ids. Existing tests don't pin these shapes.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| validate_identifier -> Ok | PASS (survives) | FAIL (killed) |
| empty check removed | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib validate_rejects_bad_identifier`.

Prepared with AI assistance; reviewed by me.

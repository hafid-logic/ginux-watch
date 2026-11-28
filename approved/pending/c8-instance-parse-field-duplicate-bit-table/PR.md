### What
Pins the `seen` bitmap bits used by `parse_field` for `[contract] allow` (bit 19) and `deny` (bit 20): repeating either key must fail with `DuplicateField`, while a single occurrence parses cleanly.

### Why it matters
`builder.mark(1 << N)` is the only duplicate guard. Shifting right (`1 >> 19 == 0`) marks bit 0, already seen from `schema_version`, so every config carrying `allow`/`deny` would be rejected as a duplicate of the wrong field. The existing duplicate test only pins `instance.id` (bit 1).

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `mark(1 << 19)` -> `mark(1 >> 19)` (contract.allow) | PASS (survives) | FAIL (killed) |
| `mark(1 << 20)` -> `mark(1 >> 20)` (contract.deny) | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-instance --lib parse_field_duplicate_detection`.

Spec-Ref: ginux instance-config parser (seen-bitmap duplicate-field contract)

Prepared with AI assistance; reviewed by me.
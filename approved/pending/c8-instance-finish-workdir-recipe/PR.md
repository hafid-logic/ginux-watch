### What
Pins `finish` bitmask defaults: explicit workdir preserved, absent workdir defaults to /work, partial contract recipe (missing default) rejected.

### Why it matters
Bit-shift errors in field masks silently ignore operator-supplied values or admit incomplete recipes. Existing tests never set workdir explicitly nor supply partial recipes.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `WORKDIR_BIT 1<<16` -> `1>>16` | PASS (survives) | FAIL (killed) |
| `RECIPE_DEFAULT_BIT 1<<38` -> `1>>38` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib finish_preserves_explicit`.

Spec-Ref: TOML config field-presence semantics (instance recipe schema)

Prepared with AI assistance; reviewed by me.

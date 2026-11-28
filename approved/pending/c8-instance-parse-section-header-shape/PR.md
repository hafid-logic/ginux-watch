### What
Pins the three shape guards at the top of `parse_section`: minimum length 3, mandatory trailing `]`, and no nested `[` inside the section name — while a minimal-length header still reaches the section match and known headers resolve.

### Why it matters
These guards run before any section dispatch; weakening them admits malformed headers into the config parser (or rejects valid minimal ones). Existing tests parse whole valid documents and never feed malformed headers directly, so the boundary and boolean mutations survive.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `line.len() < 3` -> `<= 3` | PASS (survives) | FAIL (killed) |
| `line.len() < 3` -> `== 3` | PASS (survives) | FAIL (killed) |
| first `\|\|` -> `&&` | PASS (survives) | FAIL (killed) |
| second `\|\|` -> `&&` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-instance --lib parse_section_rejects_malformed`.

Spec-Ref: ginux instance-config section header grammar

Prepared with AI assistance; reviewed by me.
### What
Pins `encode_record` rejection of invalid entries: an over-length path (`> MAX_PATH`), an over-length link (`> MAX_LINK`), and a relative path (no leading `/`) each return `InvalidPath`.

### Why it matters
The index encoder validates path/link bounds before writing a record. The existing tests only encode valid entries, so a weakened validation that admits an oversized or relative path survives them.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `|| link.len > MAX_LINK` -> `&&` | PASS (survives) | FAIL (killed) |
| `|| path.len > MAX_PATH` -> `&&` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-vfs --lib encode_record`.

Prepared with AI assistance; reviewed by me.

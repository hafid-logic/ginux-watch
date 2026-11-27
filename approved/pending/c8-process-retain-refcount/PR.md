### What
Pins `retain` via duplicate: both duplicated ends raise the count to 4, closing originals keeps the pipe alive, only the last copy frees it.

### Why it matters
Over-retaining leaks pipe objects; skipping the live check retains freed slots. Existing duplicate tests pin single-end retention, not both-ends survival.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `ends += 1` -> `ends += 2` | PASS (survives) | FAIL (killed) |
| drop `.live` check in retain | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib duplicate_retains`.

Prepared with AI assistance; reviewed by me.

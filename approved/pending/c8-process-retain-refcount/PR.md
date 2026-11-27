### What
Pins `retain` via duplicate: both duplicated ends raise the count to 4, closing originals keeps the pipe alive, only the last copy frees it.

### Why it matters
Over-retaining leaks pipe objects; skipping the increment retains nothing and under-counts duplicates. Existing duplicate tests pin single-end retention, not both-ends survival.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| no-op retain (early return) | PASS (survives) | FAIL (killed) |
| decrement instead of increment | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib duplicate_retains`.

Prepared with AI assistance; reviewed by me.

### What
Pins `pipe_ends`: pipe 0 and out-of-range ids report 0, live pipes report their end count, freed slots report 0, reused slots report fresh counts.

### Why it matters
Diagnostics drive leak checks; dropping the zero guard indexes pipe 0 - 1 (underflow) and returning 0 for live pipes misreports leaks. No existing test exercises these edges.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| disable `pipe == 0` guard | PASS (survives) | FAIL (killed) |
| return 0 for live pipes | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib pipe_ends_reports`.

Prepared with AI assistance; reviewed by me.

### What
Pins `PipeSpace` reference counting: a pipe is freed only when its last end closes. The test creates a pipe (2 ends), duplicates an end (3), then closes each end, asserting `pipe_ends` and `active_pipes` at every step.

### Why it matters
`release` decrements the end count and frees the pipe at zero. The existing tests cover duplicate origin-tracking but not the release-to-zero lifecycle, so a fault that skips release or frees early survives them.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `release`: `kind == External` -> `!=` | PASS (survives) | FAIL (killed) |
| `release`: `ends == 0` -> `!= 0` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib pipe_release`.

Prepared with AI assistance; reviewed by me.

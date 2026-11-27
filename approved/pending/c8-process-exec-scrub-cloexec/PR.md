### What
Pins `exec_scrub`: only cloexec ends are closed, their pipes released, surviving fds stay usable, and the call is idempotent.

### Why it matters
exec must drop cloexec descriptors without touching kept ones. No existing test exercises exec_scrub, so inverting the cloexec predicate or miscounting survives.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `entry.cloexec` -> `!entry.cloexec` | PASS (survives) | FAIL (killed) |
| return `0` instead of `count` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib exec_scrub_drops`.

Prepared with AI assistance; reviewed by me.

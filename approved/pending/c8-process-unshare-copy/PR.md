### What
Pins `unshare`: a shared descriptor table is copied privately (pipe ends retained), a solo task is a no-op, and unknown tasks return Ok without allocation.

### Why it matters
Exec unshares files before CLOEXEC scrub; counting zero members or off-by-one on the member threshold either leaks shared fds across exec or double-retains pipes. No existing test exercises unshare.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `**member != 0` -> `== 0` | PASS (survives) | FAIL (killed) |
| `> 1` -> `>= 1` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib unshare_copies_shared`.

Prepared with AI assistance; reviewed by me.

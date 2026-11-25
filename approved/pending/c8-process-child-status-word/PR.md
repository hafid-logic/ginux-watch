### What
Pins `ChildStatus::word`: an exited child encodes `(code & 0xff) << 8`; a signaled child encodes `signal & 0x7f`.

### Why it matters
The wait status word must match the kernel's encoding. The existing tests do not exercise `word` directly, so a shift-direction or mask fault survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| exit `<< 8` -> `>> 8` | PASS (survives) | FAIL (killed) |
| signal `& 0x7f` -> `\| 0x7f` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib child_status`.

Prepared with AI assistance; reviewed by me.

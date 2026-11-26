### What
Pins `ChildStatus::word`: an exited child encodes `(code & 0xff) << 8`; a signaled child encodes `signal & 0x7f`. Includes boundary assertions that prove the masks are necessary: `Exited(256) -> 0`, `Exited(-1) -> 255 << 8`, `Signaled(128) -> 0`, `Signaled(255) -> 127`.

### Why it matters
The wait status word must match the kernel's encoding. Without out-of-range inputs, removing either mask still passes — these boundary cases pin the masking behavior itself.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| remove `& 0xff` from Exited | PASS (survives) | FAIL (killed) |
| remove `& 0x7f` from Signaled | PASS (survives) | FAIL (killed) |
| exit `<< 8` -> `>> 8` | PASS (survives) | FAIL (killed) |
| signal `& 0x7f` -> `\| 0x7f` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib child_status`.

Prepared with AI assistance; reviewed by me.

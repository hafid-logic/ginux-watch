### What
Pins `ChildStatus::shell_code`: exited children pass their exit code through unchanged, and signaled children report the shell convention `128 + signal` (SIGKILL 9 -> 137, SIGTERM 15 -> 143).

### Why it matters
Diagnostics and shell-facing wrappers rely on this exact offset. Constant-folding the result or replacing `+` with `*`/`-` produces plausible-looking but wrong status codes. No existing test calls `shell_code`, so every mutation on it survives the current suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `shell_code -> 0` | PASS (survives) | FAIL (killed) |
| `128 + signal` -> `128 * signal` | PASS (survives) | FAIL (killed) |
| `128 + signal` -> `128 - signal` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib shell_code_pins_128`.

Spec-Ref: POSIX shell exit-status convention (128 + signal number)

Prepared with AI assistance; reviewed by me.
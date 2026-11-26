### What
Pins `balanced_arguments_allowed` for syscall 302 (prctl): admission requires `arg0 == 0` and `arg1 <= 15`; the test covers the exact boundary (15 admitted, 16 rejected) and a nonzero option.

### Why it matters
The prctl arm had no direct test. Widening the argument bound or dropping the option check would silently over-admit while passing the existing suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop `arg0 == 0` check | PASS (survives) | FAIL (killed) |
| `arg1 <= 15` -> `arg1 <= 16` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib prctl_admission`.

Prepared with AI assistance; reviewed by me.

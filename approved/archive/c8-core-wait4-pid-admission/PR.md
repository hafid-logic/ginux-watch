### What
Pins the `wait4` arm of `balanced_arguments_allowed`: pid `0` is rejected, while `-1` (`u64::MAX`) and positive pids are admitted. Also sweeps every `prot` combination for `mmap`/`mprotect` to pin W^X.

### Why it matters
`wait4(-1)` is the canonical "any child" wait and must stay admitted; pid 0 names a process group and is outside the balanced surface. The existing suite never exercises this arm, so narrowing or widening it passes unnoticed.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `arg0 > 0` -> `arg0 > 1` | PASS (survives) | FAIL (killed) |
| drop the `u64::MAX` alternative | PASS (survives) | FAIL (killed) |
| admit unconditionally (`true`) | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib mmap_mprotect_reject`.

Prepared with AI assistance; reviewed by me.

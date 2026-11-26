### What
Pins `/sys/devices/system/cpu/online`: a single CPU renders `0\n` (no range), many CPUs render `0-(count-1)\n`, and zero CPUs fail closed with `NotFound`.

### Why it matters
The range suffix and the zero guard are boundary behavior. The existing test only reads the two-CPU case, so widening the range condition to `>= 1` or removing the zero guard survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `cpu_count > 1` -> `>= 1` | PASS (survives) | FAIL (killed) |
| remove `cpu_count == 0` guard | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib sysfs_cpu_online`.

Prepared with AI assistance; reviewed by me.

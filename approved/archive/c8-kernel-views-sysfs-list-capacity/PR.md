### What
Pins `SysFs::list_devices`: the returned count is the number of devices actually copied (min of output capacity and device count), a smaller output is truncated with the prefix preserved, a larger output leaves the tail untouched, and an empty output yields 0.

### Why it matters
The projection must report copied entries, not the total. The existing tests read fixed sysfs leaves but never exercise `list_devices` capacity, so returning the full device count or dropping the capacity clamp survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| return `devices.len()` instead of copied `count` | PASS (survives) | FAIL (killed) |
| `count = output.len()` (drop the `min` clamp) | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib sysfs_list_devices`.

Prepared with AI assistance; reviewed by me.

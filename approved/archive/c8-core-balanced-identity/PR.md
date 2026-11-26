### What
Pins `balanced_identity_result`: `getpid`/`getpgrp` report the virtual pid, `getppid` reports 1, the uid/gid family reports 0, and an unknown syscall reports `None`.

### Why it matters
The balanced contract virtualizes identity. The existing tests check the uid result and the mediated tid but not the parent/group arms, so deleting either arm survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `SYS_GETPPID => Some(1)` arm | PASS (survives) | FAIL (killed) |
| delete `SYS_GETPGRP => Some(VIRTUAL_PID)` arm | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib balanced_identity`.

Prepared with AI assistance; reviewed by me.

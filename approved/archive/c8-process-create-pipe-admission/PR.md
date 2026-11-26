### What
Pins `PipeSpace::create_pipe` admission: a read or write fd that collides with an existing descriptor is rejected with `InvalidState`, a task with fewer than two free descriptor slots is rejected with `DescriptorFull` **without consuming a pipe object**, and exactly two free slots admit one more pipe.

### Why it matters
The mirror installs both ends of a host pipe pair. The existing suite exercises happy-path creation and release but never the collision guard or the two-slot requirement, so dropping either check passes it. A one-slot admission would place a single end and leak the pipe object.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop the `write_fd` collision lookup | PASS (survives) | FAIL (killed) |
| `free < 2` -> `free == 0` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib create_pipe_rejects`.

Prepared with AI assistance; reviewed by me.

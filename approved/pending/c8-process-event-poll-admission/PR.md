### What
Pins `EventPoll::add` admission: descriptor 0, zero events, unsupported mask bits, and duplicate active descriptors are rejected; valid single/combined masks accepted; freed slots reusable.

### Why it matters
Admission gates prevent invalid poll registrations that corrupt readiness reporting. Flipping `||` to `&&` admits zero-descriptor entries; XOR instead of AND-NOT misvalidates the event mask. Existing tests exercise only the happy path.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| first `||` -> `&&` | PASS (survives) | FAIL (killed) |
| `& !(...)` -> `^ (...)` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-process --lib event_poll_add_rejects`.

Spec-Ref: poll(2) / epoll_ctl(2) registration semantics

Prepared with AI assistance; reviewed by me.

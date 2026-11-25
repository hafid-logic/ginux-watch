### What
Pins `IsolatedNetwork::receive`: an empty queue returns `QueueEmpty`, a buffer smaller than the queued frame returns `InvalidPayload` without consuming it, an exact-fit buffer receives the frame, and a closed network returns `Closed`.

### Why it matters
The receive path guards buffer sizing and queue state. The existing suite sends and receives exact-fit frames but never exercises the small-buffer, empty-queue, or closed paths, so removing those guards survives it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| remove `output.len() < frame.len` guard | PASS (survives) | FAIL (killed) |
| remove `self.len == 0` guard | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib receive_rejects`.

Prepared with AI assistance; reviewed by me.

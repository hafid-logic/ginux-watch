### What
Pins two device behaviors: network `views` project major 0 with one-based minors (`slot index + 1`), and `IsolatedNetwork::receive` advances the ring head with modulo wrap so FIFO order survives a full wrap cycle.

### Why it matters
The minor number identifies the network interface to userspace; `index + 1` mutated to `index * 1` or `index - 1` shifts every interface id. The receive head `(head + 1) % FRAMES` mutated to `/` breaks wrap-around and returns stale frames. Existing view tests only cover pseudo-devices; existing receive tests never wrap the ring.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `index as u32 + 1` -> `index as u32 * 1` (network minor) | PASS (survives) | FAIL (killed) |
| `index as u32 + 1` -> `index as u32 - 1` | PASS (survives) | FAIL (killed) |
| `(head + 1) % FRAMES` -> `(head + 1) / FRAMES` | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-devices --lib network_view_minor_is_one_based`.

Spec-Ref: device view projection contract (network minor numbering); ring-buffer FIFO semantics

Prepared with AI assistance; reviewed by me.
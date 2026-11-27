### What
Pins that an unlinked overlay slot is scrubbed (data zeroed, len reset) before reuse so a fresh overlay never leaks prior bytes.

### Why it matters
Overlay reuse must not expose stale content. Existing tests cover whiteouts but not scrub-on-reuse, so dropping the scrub survives.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop `data.fill(0)` | PASS (survives) | FAIL (killed) |
| drop `len = 0` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-vfs --lib unlinked_overlay_slot`.

Prepared with AI assistance; reviewed by me.

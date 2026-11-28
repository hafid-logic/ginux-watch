### What
Pins `copy_to_overlay` size gate: exact FILE_SIZE fit copies successfully, and smaller base files also copy without rejection.

### Why it matters
Relaxing `>` to `>=` rejects valid exact-fit images; relaxing to `==` admits only exact sizes and rejects all smaller files. Existing tests never exercise the overlay copy size boundary.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `size > FILE_SIZE` -> `size >= FILE_SIZE` | PASS (survives) | FAIL (killed) |
| `size > FILE_SIZE` -> `size == FILE_SIZE` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-vfs --lib copy_to_overlay_accepts`.

Spec-Ref: overlay copy-on-write size invariant (VFS internal contract)

Prepared with AI assistance; reviewed by me.

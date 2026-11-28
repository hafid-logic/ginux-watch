### What
Pins `copy_to_overlay` size gate: exact FILE_SIZE fit copies and reads back successfully.

### Why it matters
Relaxing `>` to `>=` rejects valid exact-fit images; relaxing to `==` admits oversized data that slices out of bounds. Existing tests never exercise the exact-boundary overlay copy path.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `size > FILE_SIZE` -> `size >= FILE_SIZE` | PASS (survives) | FAIL (killed) |
| `size > FILE_SIZE` -> `size == FILE_SIZE` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-vfs --lib copy_to_overlay_accepts`.

Spec-Ref: overlay copy-on-write size invariant (VFS internal contract)

Prepared with AI assistance; reviewed by me.

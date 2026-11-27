### What
Pins `decode_record` length gates: exact MAX_PATH/MAX_LINK fit decodes, one-past-MAX_LINK and zero-length path are rejected at index load.

### Why it matters
Decode gates guard every record read; relaxing `>` to `>=` rejects valid exact-fit images, while `==` admits oversized links that later slice out of bounds. Existing tests pin encode-side and path-overflow only, not decode-side exact fit or link overflow.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| `link_len > MAX_LINK` -> `>=` | PASS (survives) | FAIL (killed) |
| `path_len > MAX_PATH` -> `==` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-vfs --lib decode_record_accepts_exact`.

Prepared with AI assistance; reviewed by me.

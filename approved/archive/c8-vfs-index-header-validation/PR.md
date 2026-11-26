### What
Pins `Index::new` header validation: a corrupted magic, an unsupported version, a wrong record size, a truncated header, and a count/length mismatch each yield `InvalidIndex`, while the well-formed index still loads.

### Why it matters
The header gates every subsequent record decode. The existing suite builds valid indices and exercises record-level bounds, but never corrupts the version or record-size fields, so dropping either check passes it and would let a foreign layout be parsed with the wrong stride.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop the `INDEX_VERSION` check | PASS (survives) | FAIL (killed) |
| drop the `RECORD_SIZE` check | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-vfs --lib index_header_rejects`.

Prepared with AI assistance; reviewed by me.

### What
Pins `loopback_netlink_ack_index`: a valid ACK matches its sequence, unknown sequences and positive acknowledgements return `None`, a message length below 16 or beyond the payload returns `Err(-22)`, a short payload returns `None`, and a non-ACK message is skipped with 4-byte alignment to reach the following ACK.

### Why it matters
The parser walks untrusted netlink payloads. The existing tests cover single well-formed messages but not the minimum-length guard or alignment across messages, so removing either survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| remove `message_length < 16` guard | PASS (survives) | FAIL (killed) |
| drop `(len + 3) & !3` alignment | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib netlink_ack_rejects`.

Prepared with AI assistance; reviewed by me.

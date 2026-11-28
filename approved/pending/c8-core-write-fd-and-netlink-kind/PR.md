### What
Pins two admission gates in ginux-core: `write(1)` admits only stdout/stderr (fd 0 and 3 rejected), and `loopback_netlink_ack_index` retires a sequence only for NLMSG_ERROR (kind 2) messages, never for other kinds.

### Why it matters
Both are fail-closed contract gates. The existing suite pins write byte counts and netlink framing/alignment but not the fd set nor the message-kind gate, so widening either passes it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| write fd set `1 \| 2` -> `0 \| 1 \| 2` | PASS (survives) | FAIL (killed) |
| drop `kind == 2` netlink gate | PASS (survives) | FAIL (killed) |

Spec-Ref: write(2) console-only surface; RFC 3549 / netlink(7) NLMSG_ERROR acknowledgement framing.

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-core --lib write_admission_rejects`.

Prepared with AI assistance; reviewed by me.


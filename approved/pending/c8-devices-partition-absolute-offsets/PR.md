Adds one unit test (12 lines) to `ginux-devices`' existing test module; **no production change**.

`Partition::range` maps a partition-relative offset to an absolute backend position. The existing partition test writes and reads through the same partition, so a constant mapping is self-consistent and invisible: replacing the whole mapping with `Ok(0)` or `Ok(1)` kept the suite green.

`partition_offsets_map_to_absolute_backend_positions` writes at partition offset `2` of a partition starting at `16` and asserts the bytes land at `backend[18..21]`, leaving `backend[0..3]` and `backend[16..18]` untouched.

**Evidence**

| run | result |
|---|---|
| baseline | `14 passed; 0 failed` |
| `range -> Ok(0)` | survives existing suite, killed only by the new test |
| `range -> Ok(1)` | survives existing suite, killed only by the new test |

Prepared with AI assistance; reviewed by me.

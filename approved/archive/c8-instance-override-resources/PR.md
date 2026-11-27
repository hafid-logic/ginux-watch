### What
Pins the `resources.memory_mib` override: value applies, exact lower bound 16 accepted, 15 rejected atomically, quoted numbers rejected.

### Why it matters
Override arms are fail-closed config gates; deleting the memory arm or its validation admits invalid configs. Existing override tests pin vcpus but never memory.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `resources.memory_mib` arm | PASS (survives) | FAIL (killed) |
| discard parsed u64 (return Ok(256)) | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib memory_override_enforces`.

Prepared with AI assistance; reviewed by me.

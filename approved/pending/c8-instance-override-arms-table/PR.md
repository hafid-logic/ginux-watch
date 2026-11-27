### What
Table-driven pin of four `apply_override_inner` arms (workdir, environment, syscalls.control=selective, catalog): values apply, unknown and derived keys fail closed.

### Why it matters
Each match arm is an operator-facing config gate; deleting any arm silently ignores overrides. Existing tests cover id/vcpus/hostname but not these four arms.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `instance.workdir` arm | PASS (survives) | FAIL (killed) |
| delete `instance.environment` arm | PASS (survives) | FAIL (killed) |
| delete `b"selective"` arm | PASS (survives) | FAIL (killed) |
| delete `contract.catalog` arm | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib override_arms_apply`.

Prepared with AI assistance; reviewed by me.

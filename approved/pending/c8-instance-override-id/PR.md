### What
Pins `apply_override` for instance.id and rejection of unknown instance keys.

### Why it matters
A deleted id arm silently ignores the override. Existing tests don't pin this arm.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `instance.id` arm | PASS (survives) | FAIL (killed) |
| id parse ignored | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib override_instance_id`.

Prepared with AI assistance; reviewed by me.

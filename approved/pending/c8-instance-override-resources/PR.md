### What
Pins `apply_override` for resources.vcpus/memory_mib and rejection of unknown keys.

### Why it matters
Override arms map keys to fields; a deleted arm silently ignores the override. Existing tests don't pin these arms.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `resources.vcpus` arm | PASS (survives) | FAIL (killed) |
| delete `resources.memory_mib` arm | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib override_resources_vcpus`.

Prepared with AI assistance; reviewed by me.

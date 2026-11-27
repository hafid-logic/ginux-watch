### What
Pins the `instance.id` override arm: quoted values apply, unknown keys and unquoted values fail closed without partial mutation.

### Why it matters
Deleting the arm or making it a no-op silently ignores operator overrides; existing tests pin vcpus/hostname but not id.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `instance.id` arm | PASS (survives) | FAIL (killed) |
| arm parses but discards value | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-instance --lib override_instance_id`.

Prepared with AI assistance; reviewed by me.

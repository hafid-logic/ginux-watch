# c8-fs-policy-path-admission-guards

Tests-only, 50 lines, existing `mod tests` in `crates/ginux-fs-policy/src/lib.rs`.
No production change. Base upstream main `30250641`.

`complete_for_path()` is the capability-completeness guard behind
`filesystem_hook_authorized`. Seven of its conjuncts had no test: replacing any
one with `true` still passed the whole existing suite.

## Surviving mutants and kills (measured, RUSTFLAGS='')

Baseline **96 passed / 0 failed** across ginux-fs-policy, -oci, -core, -contract,
-instance, -devices, -cli.

| mutant (conjunct -> `true`) | existing suite | killed by |
|---|---|---|
| `self.task.host != 0` | survives | `path_admission_requires_every_identity_dimension` |
| `self.task.virtual_id != 0` | survives | same |
| `self.task.generation != 0` | survives | same |
| `self.authority.root.kind == Root` | survives | `path_admission_requires_root_and_cwd_capability_kinds` |
| `self.authority.cwd.kind == WorkingDirectory` | survives | same |

**Equivalent mutants excluded (honest):** zeroing `instance.identity` or
`instance.lifetime` is already rejected by `Capability::authorizes`, so removing
those two conjuncts is not observable. They are asserted in the new test but are
**not** claimed as kills.

## Apply

    git am PR.patch

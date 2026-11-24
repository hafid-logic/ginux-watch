# c8-devices-revoke-instance-scope

Tests-only, 13 lines, existing `mod tests` in `crates/ginux-devices/src/lib.rs`.
No production change. Base upstream main `30250641`.

`revoke(instance)` guards both teardown loops with `instance == instance`. Neither
guard had coverage: dropping either one still passed the whole existing suite,
while making `revoke(1)` tear down instance 2's descriptors and assignments.

## Surviving mutants and kills (measured, RUSTFLAGS='')

Baseline **96 passed / 0 failed** across ginux-devices, -fs-policy, -oci, -core,
-contract, -instance, -cli.

| mutant | existing suite | killed by |
|---|---|---|
| `if descriptor.open && descriptor.instance == instance` -> `if descriptor.open` | survives | `revoke_only_tears_down_its_own_instance` |
| `if assignment.active && assignment.instance == instance` -> `if assignment.active` | survives | same |

The test separates *dead* (`InvalidDescriptor`) from *alive but denied*
(`PermissionDenied` on a zero device), so it observes descriptor liveness directly
rather than inferring it.

**Equivalent mutant excluded (honest):** dropping `entry.active` from the `assign`
conflict check is not observable, because `revoke` also zeroes the backend, so the
conflict predicate no longer matches. A test for it was written, measured as
non-killing, and removed.

## Apply

    git am PR.patch

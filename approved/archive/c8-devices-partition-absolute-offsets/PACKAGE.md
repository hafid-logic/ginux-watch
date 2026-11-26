# c8-devices-partition-absolute-offsets

- **Crate:** `ginux-devices`
- **Branch:** `tests/devices-partition-absolute-offsets` @ `02eb0908`
- **Lines:** 12 (tests only, existing `mod tests`)
- **Base:** upstream `main`

## Surviving mutants (double-measured)

| mutant | pristine main | with new test |
|---|---|---|
| `Partition::range` tail -> `Ok(0)` | survives | killed by the new test only |
| `Partition::range` tail -> `Ok(1)` | survives | killed by the new test only |

Baseline `14 passed; 0 failed`. `cargo fmt --check -p ginux-devices` clean.

## Why the gap existed

The existing partition test round-trips through the same partition, so any constant offset mapping stays self-consistent. Observing the **absolute backend bytes** exposes it.

## Apply

```bash
git am PR.patch
```

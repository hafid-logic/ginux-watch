# c8-ginux-oci-reference-guards

Tests-only. 22 lines added to the existing `mod tests` in `crates/ginux-oci/src/lib.rs`.
No production change. Base: upstream main `9f1185cf`.

## Surviving mutants (measured, RUSTFLAGS='')

Baseline: **91 passed / 0 failed** across ginux-oci, -core, -contract, -instance,
-devices, -fs-policy, -cli.

| # | single-line mutation | pre-existing suite | killed by (new test) |
|---|---|---|---|
| M1 | `hex.len() != 64` -> `hex.len() < 64` | 90 pass, survives | `reference_rejects_overlong_digest` |
| M2 | registry charset `b".-:"` -> `b".:"` | 90 pass, survives | `reference_accepts_registry_host_with_port_and_hyphen` |
| M3 | drop `&& !repository.contains('/')` | 90 pass, survives | `docker_io_nested_repository_is_not_prefixed_twice` |

Each mutant fails **exactly one** test - the new one - and no pre-existing test.

Rejected variant: dropping `:` from the registry charset was killed by the
pre-existing `cached_index_materializes_without_a_registry`, so it is not a
surviving mutant and was discarded.

## Coverage limits (honest)

`ginux-allocator` excluded: pre-existing `E0425` (`c_char` gated by
`#[cfg(not(test))]`) breaks `make test-unit` on this host. `runtime-fixture` /
`process-native-fixture` are `no_std` with private `_start` and cannot build as
test harnesses (`E0152`). Survival is therefore measured over the seven crates
above, not the full workspace.

## Apply

    git am PR.patch

`PR.patch` sha256: `109acd944be39d9fe0ec27e2d0e18d66e82c3b5a66dd5c5dc7282b83c361249d`

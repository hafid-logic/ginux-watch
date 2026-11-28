### What
Pins `remove_path`: a missing path is a successful no-op, a populated directory is removed recursively, and a symlink is unlinked without touching its target.

### Why it matters
Layer teardown must be idempotent and complete. The existing suite exercises whiteouts over present entries only, so failing on a missing path or dropping recursion passes it while leaving stale layer content or aborting an import.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| NotFound arm returns Err instead of Ok | PASS (survives) | FAIL (killed) |
| `remove_dir_all` -> `remove_dir` | PASS (survives) | FAIL (killed) |

Spec-Ref: OCI image-spec layer whiteout application (idempotent removal).

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-oci --lib remove_path_unlinks`.

Prepared with AI assistance; reviewed by me.


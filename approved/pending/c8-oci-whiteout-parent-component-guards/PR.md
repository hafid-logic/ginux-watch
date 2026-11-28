### What
Pins `safe_whiteout_dir` traversal rules: any non-Normal path component (`./`, `../`, absolute prefix) is rejected, while not-yet-existing normal directories are tolerated and an empty parent resolves to the extraction root.

### Why it matters
This guard is the security boundary keeping OCI whiteouts inside the rootfs. Accepting `Component::CurDir`/`ParentDir` would let a crafted layer walk out of the root; rejecting missing directories would break legitimate layers that create parents later. The existing symlink test only covers the symlink branch, so these mutations survive.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| accept all components (`_ => {}`) | PASS (survives) | FAIL (killed) |
| treat NotFound as fatal | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-oci --lib safe_whiteout_dir_rejects_non_normal`.

Spec-Ref: OCI image-spec layer whiteout application (path traversal containment)

Prepared with AI assistance; reviewed by me.
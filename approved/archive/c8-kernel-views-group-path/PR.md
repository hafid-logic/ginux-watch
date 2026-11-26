### What
Pins `validate_group_path` via `create`: trailing slash, double slash, `..` segment, space/semicolon charset, empty, relative, and over-length paths are each `InvalidPath`; a valid name with dot/dash/underscore is accepted.

### Why it matters
Group paths name virtual cgroup directories; the validator is the traversal/charset gate. The existing tests only exercise one `..` case, so dropping the trailing-slash or charset clause survives the suite.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| drop `ends_with(b"/")` clause | PASS (survives) | FAIL (killed) |
| drop ASCII charset clause | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib group_path_validation`.

Prepared with AI assistance; reviewed by me.

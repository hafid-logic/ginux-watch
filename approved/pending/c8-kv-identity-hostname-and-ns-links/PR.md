### What
Pins three IdentityFs arms: reading `/etc/hostname` returns the instance hostname with a trailing newline, and `readlink` on `ns/pid` / `ns/uts` renders `pid:[id]` / `uts:[id]` with the instance-owned namespace ids.

### Why it matters
Userspace reads hostname and namespace links to detect isolation. Deleting any of these match arms turns a valid path into NotFound, breaking hostname resolution and namespace introspection. The existing identity test pins machine-id, ns/mnt and ns/cgroup only, so all three deletions survive it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `/etc/hostname` read arm | PASS (survives) | FAIL (killed) |
| delete `ns/pid` readlink arm | PASS (survives) | FAIL (killed) |
| delete `ns/uts` readlink arm | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-kernel-views --lib identity_hostname_read_and_pid_uts`.

Spec-Ref: proc(5) namespace symlinks (ns/pid, ns/uts); hostname(7) via /etc/hostname

Prepared with AI assistance; reviewed by me.
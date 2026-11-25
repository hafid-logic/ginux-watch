# T: cgroup subtree controller parsing (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-kernel-views · File: crates/ginux-kernel-views/src/cgroup.rs
Evidence:
- `cgroup.rs:288:22: replace |= with &= in parse_controllers`
- delete match arms `b"+cpu"`, `b"+memory"`, `b"+pids"`, `b""` in parse_controllers
- `cgroup.rs:288:41: replace == with != in parse_controllers`

Why it matters: decides which controllers are enabled in cgroup.subtree_control.
Wrong parsing silently drops or misapplies a controller => confinement gap.

Next action: one test asserting exact controller sets for mixed +/- input and
rejection of unknown/empty tokens. Exclude equivalent mutants explicitly.

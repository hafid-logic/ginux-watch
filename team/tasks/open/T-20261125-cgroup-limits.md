# T: cgroup limit parsing (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-kernel-views · File: crates/ginux-kernel-views/src/cgroup.rs
Evidence:
- `cgroup.rs:270:14: replace == with != in parse_limit_u64`
- `cgroup.rs:270:5: replace parse_limit_u64 -> Result<u64, ViewError> with Ok(1)`
- `cgroup.rs:278:5: replace parse_limit_u32 -> Result<u32, ViewError> with Ok(0)` / `Ok(1)`

Why it matters: these parse cgroup resource limits (e.g. pids.max / memory.max).
Accepting a malformed limit or returning a constant weakens confinement.

Next action: table-driven test over accepted ("max", decimal) and rejected (empty,
non-digit, overflow, negative) forms. Verify non-equivalence before claiming kills.

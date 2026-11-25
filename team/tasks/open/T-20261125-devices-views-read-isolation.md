# T: DeviceRegistry views/read cross-instance guards (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-devices
Evidence (cargo-mutants scan.log, harvested 2026-11-25):
- lib.rs:190: replace && with ||
- lib.rs:192: replace == with !=
- lib.rs:266: replace ^= with |=
- lib.rs:266: replace << with >>

Why it matters: views/read aggregate device data; dropping an instance/kind guard cross-serves another instance's descriptors - isolation gap.

Next action: one focused test in the existing mod tests killing the listed guards; baseline green, mutants survive old suite, new test kills them, <=60 lines, fmt clean.

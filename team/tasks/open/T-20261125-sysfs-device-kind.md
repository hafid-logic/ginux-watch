# T: SysFs device-kind read guards (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-kernel-views · File: crates/ginux-kernel-views/src/lib.rs
Evidence (cargo-mutants missed.txt):
- `lib.rs:166:20: replace match guard device.kind != DeviceKind::Network with true in SysFs::read`
- `lib.rs:172:20: replace match guard device.kind == DeviceKind::Network with true in SysFs::read`

Why it matters: `dev` (major:minor) is served only for non-network devices and `type`
only for network ones. Forcing either guard true cross-serves device data between
kinds — an isolation/correctness gap, not cosmetics.

Next action: one test in the existing `mod tests` exercising a Network and a non-Network
assignment through `SysFs::read` for both leaves; assert NotFound for the wrong pairing.
Gate: baseline green, both mutants survive the old suite, new test kills both, <=60 lines, fmt clean.

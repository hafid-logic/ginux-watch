### What
Pins the third batch of `apply_override_inner` match arms: `contract.devices.read/.write/.create`, `contract.process.signals` and `contract.kernel.proc_read` each apply their parsed list to the matching field, and a non-empty device create list flips `filesystem_device_nodes`.

### Why it matters
Each arm is an independent security-policy channel. A deleted arm silently ignores the operator's override while returning success, so a device or kernel rule would never take effect. The existing suite pins batch 1 (#370) and the filesystem batch (#385) but not these five arms.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| delete `contract.devices.read` arm | PASS (survives) | FAIL (killed) |
| delete `contract.devices.create` arm | PASS (survives) | FAIL (killed) |
| delete `contract.process.signals` arm | PASS (survives) | FAIL (killed) |
| delete `contract.kernel.proc_read` arm | PASS (survives) | FAIL (killed) |

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-instance --lib override_policy_channels`.

Spec-Ref: ginux instance-config override contract (device/process/kernel policy channels)

Prepared with AI assistance; reviewed by me.
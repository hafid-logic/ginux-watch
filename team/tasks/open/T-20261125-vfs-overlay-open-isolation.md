# T: VirtualFs open/overlay isolation guards (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-vfs
Evidence (cargo-mutants scan.log, harvested 2026-11-25):
- lib.rs:373: replace & with ^
- lib.rs:373: replace & with |
- lib.rs:622: replace match guard self.overlay[slot].state == 2 && !self.referenced(slot) with false
- lib.rs:622: replace == with !=

Why it matters: open and overlay copy/create guards gate which layer serves a path; forcing them true bypasses overlay isolation - access-control gap.

Next action: one focused test in the existing mod tests killing the listed guards; baseline green, mutants survive old suite, new test kills them, <=60 lines, fmt clean.

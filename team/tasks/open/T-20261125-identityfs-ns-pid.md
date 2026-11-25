# T: IdentityFs readlink ns/pid arm (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-kernel-views · File: crates/ginux-kernel-views/src/lib.rs
Evidence: `lib.rs:80:9: delete match arm b"ns/pid" in IdentityFs::readlink`

Why it matters: namespace pid link is part of the virtual identity a task sees.
Dropping it changes identity resolution rather than formatting.

Next action: assert readlink for ns/pid returns the virtual pid and that unknown
leaves still fail closed.

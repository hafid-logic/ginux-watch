# T: PipeSpace release/retain/pipe_ends lifecycle guards (READY TO BUILD)

Status: **discovered, measured, not started**
Crate: ginux-process
Evidence (cargo-mutants scan.log, harvested 2026-11-25):
- lib.rs:1321: replace || with &&
- lib.rs:1321: replace == with !=
- lib.rs:1314: replace - with +
- lib.rs:1314: replace - with /

Why it matters: pipe end lifecycle and retention guards; a wrong predicate leaks or double-frees pipe ends across tasks - confinement gap.

Next action: one focused test in the existing mod tests killing the listed guards; baseline green, mutants survive old suite, new test kills them, <=60 lines, fmt clean.

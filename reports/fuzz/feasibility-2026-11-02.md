# 2a) Feasibility study — fuzzing upstream `crates/oci` surfaces (2026-11-02)

> **Reconstruction note:** the original version of this report was committed in
> a commit that was lost with a sandbox recycle on 2026-11-02 (it was pushed
> nowhere and died with the instance). This file is restored from the session
> records of that study; measurements attributed below to 2026-11-02 were
> actually taken in the lost session and are quoted as recorded there. New
> verification done today is tagged `[MEASURED 2026-11-02T09:xxZ]`.

## Question (2a)

Can we fuzz the parser surfaces of upstream `crates/oci` (tar/PAX rootfs,
registry manifest, image reference, bearer auth, digest validation) **without
modifying upstream in any way**, from our own repository, with results
trustworthy enough to act on?

## Answer

**Feasible — adopted.** The harness lives in `fuzz/` (target `oci_surfaces`),
upstream is consumed through a pinned, read-only path dependency, and the
runbook is `fuzz/README.md`. CI wiring: `.github/workflows/fuzz.yml`
(weekly Mondays 05:30 UTC + manual dispatch, 25-minute budget, `contents: read`,
no persisted credentials, upstream pinned at `ecbb3142e0c332…`).

## Constraints discovered (each was a real failure before being understood)

1. cargo-fuzz 0.13.2 requires a root `Cargo.toml` → virtual manifest, no
   members (member-izing upstream crates breaks their workspace inheritance).
2. `[package.metadata] cargo-fuzz = true` required in `fuzz/Cargo.toml`.
3. Default target is musl; the libFuzzer runtime needs C++ → build explicitly
   with `--target x86_64-unknown-linux-gnu` and install `g++`.
4. Nightly with `rust-src` + `llvm-tools-preview` for `-Zbuild-std` and
   coverage instrumentation.

## Verification record

- Lost session [MEASURED, quoted]: `cargo fuzz build` succeeded; a 15-second
  live run over the seed corpus produced no crashes; corpus/artifacts layout
  validated; local quirk `unset CPATH` recorded (stale sysroot path breaks the
  C++ compile — CI unaffected).
- Today [MEASURED 2026-11-02T09:xxZ]: files restored 1:1 from session records;
  `cargo check` of the fuzz crate re-run against upstream `ecbb3142` — result
  recorded in reports/2026-11-02.md (section Session 6).

## Non-goals

- No fuzzing of the kernel itself (unsafe-heavy, needs QEMU-in-the-loop; a
  later study may pair libFuzzer with the existing ginux-verify boot matrix).
- No upstream PRs from fuzz findings: findings follow POLICY.md (draft first,
  explicit user approval before any upstream publication).

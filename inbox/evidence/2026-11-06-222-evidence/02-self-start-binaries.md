# Evidence memo 2/3 — self-start binaries & unit/native suites with
# `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` vs baseline (request from #222 owner reply)

**Status: prepared locally, NOT published.** Owner request (#222, 05:29:33Z):
"the self-start binaries ... remain open" — i.e., do the self-start/freestanding
binaries and the test suites still hold up with overflow checks restored?

**Protocol [MEASURED]** — GitHub Actions workflow `probe-overflow-evidence.yml`,
run **42178425135** (all three jobs success), our repo, upstream cloned at
pinned main head `3f2fe7df`, read-only wrt upstream:
- baseline = upstream tree untouched (no `overflow-checks` key);
- flag = same SHA, `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` env (profile
  override, no file modified) — byte-identical source, only the profile knob;
- same runner image per comparison (ubuntu-24.04; macos-15 arm64 second axis).

## Results — ubuntu-24.04

| Check | Baseline | Flag | Tag |
|---|---|---|---|
| `make test-unit` (7 crates) | **65/65 pass** | **65/65 pass** | MEASURED (runs 1–4) |
| `make build` + fixtures (self-start bins) | PASS | PASS | MEASURED |
| `sudo make test-launch` | **PASS** | **PASS** | MEASURED |
| `sudo make test-native-supervision` | **PASS** | **PASS** | MEASURED |
| `make test-process-native` | **PASS** | **PASS** | MEASURED |

## Results — macOS arm64 (macos-15, aarch64-apple-darwin)

| Check | Baseline | Flag | Tag |
|---|---|---|---|
| `make test-unit` | **65/65 pass** | **65/65 pass** | MEASURED (runs 2–4) |
| regression canary C1 (release, no flag) | — | FAILS as expected (exit 101) | MEASURED (runs 2–4) |
| regression canary C2 (release + flag) | — | PASSES (exit 0) | MEASURED (runs 2–4) |
| `ginux-init` build on aarch64 | **does not compile** (43 errors, both modes) | same | MEASURED — honest negative: the freestanding init is x86_64-specific; not a flag regression |
| `ginux-vfs-index` release sizes on macOS | not captured (build step aborts with ginux-init) | same | stated as not captured |
| launch/native supervision | not applicable | not applicable | linux-specific (namespaces/ptrace fixtures); stated as not run on macOS |

## Regression canary (release-only)

| Run | Build | Expected | Result |
|---|---|---|---|
| C1 release, no flag (pristine main) | canary `overflow_checks_release.rs` | FAIL (silent wrap) | **exit 101** on ubuntu-24.04 and macOS arm64 — defect reproduced [MEASURED] |
| C2 release, flag | same | PASS | **exit 0** on ubuntu-24.04 and macOS arm64 [MEASURED] |
| C3 debug, no flag | same | PASS either way (debug cannot detect) | exit 0 on ubuntu-24.04 [MEASURED] |

Debug runs cannot detect the regression: overflow-checks are on by default in
dev profiles, so `make test-unit` (debug) stays green even when the release
setting is absent. Only a `--release` test run discriminates — this is why the
loss of the setting went unnoticed since the #152 transition.

## Linking deviation note (transparency)

Upstream `.cargo/config.toml` links the linux-gnu target with rust-lld +
`-nostdlib/-static` for the freestanding bins. The self-start bins build and
link under that config on the runners (and locally). The std tooling crate
`ginux-vfs-index` cannot be linked by that config (no std libc resolution) —
upstream CI never links it either; our probe builds it with
`RUSTFLAGS="-C linker=cc"` (documented deviation, linker-only). This does not
affect the overflow-checks comparison: both sides of every table above use the
same link mode.

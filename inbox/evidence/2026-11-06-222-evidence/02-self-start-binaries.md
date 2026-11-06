# Evidence memo 2/3 — self-start binaries & unit/native suites with
# `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` vs baseline (request from #222 owner reply)

**Status: prepared locally, NOT published.** Owner request (#222, 05:29:33Z):
"the self-start binaries ... remain open" — i.e., do the self-start/freestanding
binaries and the test suites still hold up with overflow checks restored?

**Protocol [MEASURED]** — GitHub Actions workflow `probe-overflow-evidence.yml`
(run: see STATE for run id), our repo, upstream cloned at pinned main head
`3f2fe7df`, read-only wrt upstream:
- baseline = upstream tree untouched (no `overflow-checks` key);
- flag = same SHA, `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` env (profile
  override, no file modified) — byte-identical source, only the profile knob;
- same runner image per comparison (ubuntu-24.04; macos-15 arm64 second axis).

## Results — ubuntu-24.04

| Check | Baseline | Flag | Tag |
|---|---|---|---|
| `make test-unit` (7 crates) | **65/65 pass** | **65/65 pass** | MEASURED (run 1 & 2) |
| `make build` + fixtures (self-start bins) | PASS | PASS | MEASURED |
| `sudo make test-launch` | **PASS** | **PASS** | MEASURED |
| `sudo make test-native-supervision` | **PASS** | **PASS** | MEASURED |
| `make test-process-native` | **PASS** | **PASS** | MEASURED |

## Results — macOS arm64 (macos-15, aarch64-apple-darwin)

| Check | Baseline | Flag | Tag |
|---|---|---|---|
| release builds `ginux` + `ginux-vfs-index` | PASS | PASS | MEASURED |
| binary sizes | see memo 3 | see memo 3 | MEASURED |
| `make test-unit` | see below | see below | — |
| launch/native supervision | not applicable | not applicable | linux-specific (namespaces/ptrace fixtures); stated as not run on macOS |

## Regression canary (release-only)

| Run | Build | Expected | Result |
|---|---|---|---|
| C1 release, no flag (pristine main) | canary `overflow_checks_release.rs` | FAIL (silent wrap) | see run log — MEASURED |
| C2 release, flag | same | PASS | see run log — MEASURED |
| C3 debug, no flag | same | PASS either way (debug cannot detect) | MEASURED |

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

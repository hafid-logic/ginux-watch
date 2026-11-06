# PR draft — Restore `overflow-checks = true` in `[profile.release]` + release canary

**Status: DRAFT — NOT PUBLISHED. Publication is Abdelhafid's manual call, by hand.**
**Prepared:** 2026-11-06 (directive v5.3-4) | **Head SHA (gate ب):** `3f2fe7dfadd4b40e235d982a6a3d386dc6490177` (upstream main, confirmed 06:3xZ)

## Gate checklist (POLICY v5.2-1, items أ–د)

- **(أ) no file+hunk overlap with an open PR** [MEASURED via API]:
  - #207 (open): files = README.md, ginux-core/src/lib.rs, ginux-init/{channel_hooks,dispatch,launch,main}.rs, scripts/test-launch.py, tests/fixtures/launch-fixture.c → **zero overlap** with Cargo.toml / Makefile / crates/ginux-vfs-index/tests/*.
  - #221: merged 2026-11-06T05:28:45Z (no longer open; its Makefile hunk is the build-process-fixtures scenario list @:58 — disjoint from our test-release-overflow target @:94+).
- **(ب) defect reproduced on main head at submission moment** [MEASURED]:
  - `CARGO_PROFILE_RELEASE_PANIC=unwind RUSTFLAGS="-C linker=cc" cargo test --release -p ginux-vfs-index --test overflow_checks_release` on pristine `3f2fe7df` → **FAILED** with "overflow checks are NOT active in this profile: intentional u64::MAX + 1 wrapped silently" (exit 101; child exited 0). Local run + Actions probe run both reproduce.
- **(ج) clean rebase:** branch is cut from `3f2fe7df` (main head) by construction; diff = 3 files, +67 lines, zero removals → cannot conflict.
- **(د) last-7-days duplicate check (raw+dump+search together)** [MEASURED]:
  - search `overflow-checks` (repo-wide): 10 hits; only open item = **#222 itself**; all else closed.
  - search `overflow created:>2026-10-30`: #222/#54/#43/#84/#82/#47/#52 — none open, none discussing vfs-index overflow.
  - **Precedent found:** PR **#54** "Enable overflow checks in release builds" — **authored by gmkurtzer, MERGED 2026-11-03T22:00:13Z**, added the exact line `overflow-checks = true` to `[profile.release]`. The transition PR **#152** (merged 2026-11-04T23:15:51Z) replaced Cargo.toml from the userspace source `2306c2e` which predates #54 — the setting was lost in the transition, exactly as the maintainer reconstructed in his #222 reply.

## The diff (PR.diff, +67/-0, 3 files)

1. `Cargo.toml`: `overflow-checks = true` — the exact line #54 merged.
2. `Makefile`: 2-line `test-release-overflow` target (within the ≤~10-line CI budget stated in directive v5.3-4).
3. `crates/ginux-vfs-index/tests/overflow_checks_release.rs`: release-only canary (63 lines, self-contained).

## Why the canary is shaped this way

- `panic = "abort"` in the release profile makes `#[should_panic]` unusable (a panicking test aborts the harness instead of unwinding into it); the canary re-executes the test binary as a child and asserts the child does NOT survive an intentional `u64` overflow, pinning the panic message.
- **Debug tests cannot detect this regression** (overflow-checks default on in dev) — the canary passes in debug both before and after; only `cargo test --release` discriminates. `make test-unit` (debug-only) therefore stays green on main, which is why the regression went unnoticed.
- Canonical invocation (also the Makefile target): `RUSTFLAGS='-C linker=cc' CARGO_TARGET_DIR=.artifacts/unit cargo test --release -p ginux-vfs-index --test overflow_checks_release`. The `RUSTFLAGS` top-precedence override is needed because upstream `.cargo/config.toml` injects freestanding link flags (rust-lld/-nostdlib/-static) meant for the self-start bins, which break std test binaries (locally MEASURED as SIGSEGV-at-startup; on runners C1/C2 in the probe validate the invocation).

## Evidence available to cite in the PR body

1. **65/65**: `make test-unit` passes with the flag (and baseline) on ubuntu-24.04 + macOS arm64 [probe run — see inbox/evidence/2026-11-06-222-evidence/02-self-start-binaries.md].
2. **Matrix**: `scan_layer` adversarial matrix — no defect found within the matrix [01-scan-layer-evidence.md].
3. **Binaries**: self-start + tooling sizes with/without flag [03-release-runtime-cost.md].
4. **Cost**: release sizes (bytes) + vfs-index scan timing (median/range, alternating runs) [03-release-runtime-cost.md].

## PR text (English — verbatim candidate body)

> **Title:** Restore `overflow-checks = true` in `[profile.release]` (+ release-only regression canary)
>
> This restores the release-profile overflow checks that were lost in the architecture transition, and adds a small release-only canary so the setting cannot silently regress again. Follows up on #222.
>
> **Provenance.** PR #54 ("Enable overflow checks in release builds") added `overflow-checks = true` to `[profile.release]` and was merged 2026-11-03. The userspace-kernel transition (#152) then replaced the manifest from the new source tree, which predated that change, so the setting was dropped without a documented decision — as reconstructed in the maintainer's reply on #222 ("the removal was not documented as an intentional overflow-policy decision ... I found no rationale ... saying release overflow checks were deliberately disabled").
>
> **What this PR does.**
> 1. Restores the exact line from #54: `overflow-checks = true` under `[profile.release]`.
> 2. Adds `crates/ginux-vfs-index/tests/overflow_checks_release.rs`: a release-only canary that fails when the setting is absent and passes when present. Because the release profile sets `panic = "abort"`, a `#[should_panic]` cannot observe the panic; the canary instead re-executes the test binary as a child process and asserts the child does not survive an intentional `u64::MAX + 1`. Note that **debug test runs cannot detect this regression** (overflow checks are on by default in dev profiles), which is why `make test-unit` never caught it — only a `--release` test run discriminates.
> 3. Adds a 2-line `make test-release-overflow` target running the canary under release.
>
> **Measured evidence that the cost is small** (full numbers in the thread-ready evidence pack):
> - Unit suite: `make test-unit` 65/65 passing with the flag on ubuntu-24.04 and macOS arm64 (probe, pinned SHA).
> - Self-start and tooling binaries: release size delta with the flag is +296 bytes on `ginux` (+0.24%) and +1,608 bytes on `ginux-vfs-index` (+0.46%) locally; runner reference numbers in the evidence pack.
> - `ginux-vfs-index` scan over a generated 50k-entry tar (220 MiB): median 112.5 ms → 117.4 ms (+4.9 ms) over 12 alternating runs per build on one machine.
> - `scan_layer` sites flagged in #222: adversarial matrix executed (max-octal / base-256 / truncated-declared-size / EFBIG bound) — no defect found within the matrix; memo with limits available.
>
> **Runners.** ubuntu-24.04 (unit, launch, native supervision, canary, sizes, timing) and macOS arm64/macos-15 (unit, canary, sizes) were exercised on the pinned SHA; the Rocky 10.2 VM targets (test-intercept, test-runtime, image tests) were NOT exercised — they require the Rocky host environment which the probe does not provision.
>
> Prepared with AI assistance (Claude); reviewed and submitted by a human.
> Nothing under this account was published automatically; this PR is opened manually by the maintainer-account holder.

## Conflict + duplication notes for the reviewer (Abdelhafid)

- The `RUSTFLAGS='-C linker=cc'` in the Makefile target is the piece I least like: it exists only because upstream `.cargo/config.toml` attaches freestanding link flags to the linux-gnu target and they break std test binaries. If the runner probe shows a cleaner override works, swap it in before publishing.
- If you prefer no Makefile touch at all, drop hunk 2; the canary still runs via the documented cargo invocation. (Directive asked to state the CI cost explicitly: it is 2 lines.)
- Circuit-breaker check before publish: #222 comments must still be 1 (owner reply only), no change-request on any of our PRs.

# PR draft — Restore `overflow-checks = true` in `[profile.release]` + release-only regression test

**Status: DRAFT — NOT PUBLISHED. Publication is Abdelhafid's manual call, by hand.**
**Prepared:** 2026-11-06 (v5.3-4) | **Updated (v5.5, session 40):** child-process canary replaced by a plain `#[should_panic]` regression test (A/B MEASURED on the pinned SHA); Makefile command unified with the `test-unit` lines (`RUSTFLAGS=''`, linker override omitted — reason below); Actions re-run dispatched with the final command.
**Head SHA (gate ب):** `3f2fe7dfadd4b40e235d982a6a3d386dc6490177` (upstream main, re-confirmed 07:5xZ via `git ls-remote` — v5.4 session)

## Gate checklist (POLICY v5.2-1, items أ–د)

- **(أ) no file+hunk overlap with an open PR** [MEASURED via API]:
  - #207 (open): files = README.md, ginux-core/src/lib.rs, ginux-init/{channel_hooks,dispatch,launch,main}.rs, scripts/test-launch.py, tests/fixtures/launch-fixture.c → **zero overlap** with Cargo.toml / Makefile / crates/ginux-vfs-index/tests/*.
  - #221: merged 2026-11-06T05:28:45Z (no longer open; its Makefile hunk is the build-process-fixtures scenario list @:58 — disjoint from our test-release-overflow target @:94+).
- **(ب) defect reproduced on main head at submission moment** [MEASURED, v5.5 A/B on pristine `3f2fe7df`, rustc 1.99.0, same command ± env flag]:
  - `RUSTFLAGS='' CARGO_TARGET_DIR=<ext> cargo test --release -p ginux-vfs-index --test overflow_checks_release` (no flag) → **FAILED**, exit 101, literal: `note: test did not panic as expected at crates/ginux-vfs-index/tests/overflow_checks_release.rs:16:4`.
  - same + `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` → **ok. 1 passed**, exit 0.
  - Local run reproduced both directions; Actions re-run with the final command dispatched (see reviewer notes).
- **(ج) clean rebase:** branch is cut from `3f2fe7df` (main head) by construction; diff = 3 files, +24 lines, zero removals → cannot conflict.
- **(د) last-7-days duplicate check (raw+dump+search together)** [MEASURED]:
  - search `overflow-checks` (repo-wide): 10 hits; only open item = **#222 itself**; all else closed.
  - search `overflow created:>2026-10-30`: #222/#54/#43/#84/#82/#47/#52 — none open, none discussing vfs-index overflow.
  - **Precedent found:** PR **#54** "Enable overflow checks in release builds" — **authored by gmkurtzer, MERGED 2026-11-03T22:00:13Z** (title re-verified live via HTML in session 40), added the exact line `overflow-checks = true` to `[profile.release]`. The transition PR **#152** (merged 2026-11-04T23:15:51Z) replaced Cargo.toml from the userspace source `2306c2e` which predates #54 — the setting was not carried across the architecture transition, exactly as the maintainer reconstructed in his #222 reply.

## The diff (PR.diff, +24/-0, 3 files)

1. `Cargo.toml`: `overflow-checks = true` — the exact line #54 merged.
2. `Makefile`: 2 content lines — `test-release-overflow:` declaration (column 0, as make requires) + **one recipe line starting with a literal TAB byte (0x09, byte-verified)**, using the same `RUSTFLAGS=''` convention as the `test-unit` lines directly above.
3. `crates/ginux-vfs-index/tests/overflow_checks_release.rs`: 20-line release-only `#[should_panic]` regression test (replaces the 63-line child-process canary per v5.5-2).

## Why the test is shaped this way (v5.5)

- `cargo test` builds test targets with `panic = "unwind"` even though `[profile.release]` sets `panic = "abort"` — so a plain `#[should_panic]` observes the overflow panic. **MEASURED A/B on the pinned SHA (rustc 1.99.0, `.cargo/config.toml` untouched):** no flag → FAILED/101 ("test did not panic as expected"); flag → ok/0. No "`panic` setting is ignored" warning was printed on 1.99.0 — the test doc-comment therefore claims nothing about a warning.
- **Debug tests cannot detect this regression** (overflow-checks default on in dev) — the test passes in debug both before and after; only `cargo test --release` discriminates. `make test-unit` (debug-only) therefore stays green on main, which is why the regression went unnoticed.
- **Makefile command unified with `test-unit` (`RUSTFLAGS=''`); `-C linker=cc` omitted — reason:** an empty-but-set `RUSTFLAGS` env var overrides the freestanding target rustflags injected by `.cargo/config.toml` (the same mechanism every `test-unit` line already relies on), and the linux-gnu default linker is `cc` anyway, so an explicit linker override is redundant. Linking with the unified command is MEASURED locally with `config.toml` untouched (both A and B runs above). Canonical invocation = the Makefile target itself.

## Evidence available to cite in the PR body

1. **65/65**: `make test-unit` passes with the flag (and baseline) on ubuntu-24.04 + macOS arm64 [probe run — see inbox/evidence/2026-11-06-222-evidence/02-self-start-binaries.md].
2. **A/B canary (v5.5)**: fails on pristine main (exit 101), passes with the flag (exit 0) — measured locally on `3f2fe7df`; Actions re-run with the final command dispatched in session 40.
3. **Matrix**: `scan_layer` adversarial matrix — no defect found within the matrix [01-scan-layer-evidence.md].
4. **Binaries + cost**: self-start + tooling sizes with/without flag; scan timing (median/range, alternating runs) [03-release-runtime-cost.md].

## PR text (English — verbatim candidate body, ≤250 words)

> **Title:** Restore `overflow-checks = true` in `[profile.release]` (+ release-only regression test)
>
> This restores `overflow-checks = true` under `[profile.release]` — the exact line PR #54 ("Enable overflow checks in release builds", merged 2026-11-03) added. The setting was not carried across the architecture transition (#152) and carries no documented decision either way. Refs #222.
>
> The added test (`crates/ginux-vfs-index/tests/overflow_checks_release.rs`) is one `#[should_panic]` on an intentional `u64::MAX + 1`. `cargo test` builds test targets with `panic = "unwind"` even when the release profile sets `panic = "abort"`, so it works under `cargo test --release`: with the flag it passes; on pristine main the add wraps silently and the test fails (exit 101). Debug runs cannot detect the regression (overflow checks are on by default in dev) — only `--release` discriminates.
>
> A 2-line `make test-release-overflow` target runs it with the same `RUSTFLAGS=''` convention as `test-unit`. Known limitation, stated explicitly: the target is not wired into `make check` or CI; wiring it in is a ≤3-line follow-up proposed separately.
>
> Measured at SHA 3f2fe7df: `make test-unit` 65/65 with the flag on ubuntu-24.04 and macOS arm64; the test fails on pristine main and passes with the flag; `ginux` 122,720 → 122,680 bytes (−40; runner-side cause not established); `ginux-vfs-index` +1,608 (+0.46%); scan timing median 223.2 → 222.5 ms (ranges 221.0–225.9 / 219.2–228.2, overlapping). Rocky VM targets were not exercised. Numbers, variance, limits: https://github.com/hafid-logic/ginux-watch/blob/c1c4948c0314dda1336d9ae5d961a9b101201348/inbox/evidence/2026-11-06-222-evidence/03-release-runtime-cost.md. Prepared with AI assistance; reviewed by me

## Conflict + duplication notes for the reviewer (Abdelhafid)

- v5.5 resolved the old `RUSTFLAGS='-C linker=cc'` concern by measurement: the unified `RUSTFLAGS=''` command links and discriminates with `.cargo/config.toml` untouched (A/B above); the Actions re-run in session 40 repeats it on the runner.
- Separate follow-up item (not in this PR): wire `test-release-overflow` into the CI job's run list — a ≤3-line addition, proposable once this lands.
- If you prefer no Makefile touch at all, drop hunk 2; the test still runs via the documented cargo invocation. (Directive asked to state the CI cost explicitly: it is 2 lines.)
- Circuit-breaker check before publish: #222 comments must still be 1 (owner reply only), #207 must have no activity after 2026-11-06T07:5xZ; re-check live immediately before posting.

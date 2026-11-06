# PR draft — Restore `overflow-checks = true` in `[profile.release]` + release-only regression test

**Status: DRAFT — NOT PUBLISHED. Publication is Abdelhafid's manual call, by hand.**
**Prepared:** 2026-11-06 (v5.3-4) | **Updated (v5.5, session 40):** child-process canary replaced by a plain `#[should_panic]` regression test (A/B MEASURED on the pinned SHA); Makefile command unified with the `test-unit` lines (`RUSTFLAGS=''`, linker override omitted — reason below). | **Updated (v5.6, session 41):** v5.5 dispatch COMPLETED (run 42195146548): C1=101/C2=0/C3=0 on the runner, 65/65 both modes both OSes, sizes byte-identical, timing 203.0→200.1 ms — PR body numbers switched to this same-run A/B (cross-run medians not comparable); AI disclosure set to the exact v5.6 string; evidence permalink re-pinned to `8f855b7d`.
**Head SHA (gate ب):** `3f2fe7dfadd4b40e235d982a6a3d386dc6490177` (upstream main, re-confirmed live via `git ls-remote` in session 42 ~11:0xZ; Cargo.toml/Makefile sha256-identical to pinned copies re-checked this session)
**Updated (v5.7, session 42):** PR branch `restore-overflow-checks` CUT at `3f2fe7df` — diff applied and re-verified byte-identical (`git -c core.abbrev=7 diff --cached` ≡ PR.diff, sha256 `3d4e8cc4…f1ab`, +24/−0, 3 files); commit message = PR title verbatim; local head `9ac0f544f7f1609cd5846e5ff97de96eff17f8cf`. **Push to the fork PENDING — no gh auth in the session-42 sandbox (old token retired per D3); Abdelhafid pushes by hand: `git push origin restore-overflow-checks` (single push, no force); do NOT open the PR.** Memo-03 permalink below re-pinned to `4b73834650847e39b58996a4c05368fd791b4ace` (launch/native cross-reference appended, nothing else changed).

## Gate checklist (POLICY v5.2-1, items أ–د)

- **(أ) no file+hunk overlap with an open PR** [MEASURED via API]:
  - #207 (open): files = README.md, ginux-core/src/lib.rs, ginux-init/{channel_hooks,dispatch,launch,main}.rs, scripts/test-launch.py, tests/fixtures/launch-fixture.c → **zero overlap** with Cargo.toml / Makefile / crates/ginux-vfs-index/tests/*.
  - #221: merged 2026-11-06T05:28:45Z (no longer open; its Makefile hunk is the build-process-fixtures scenario list @:58 — disjoint from our test-release-overflow target @:94+).
- **(ب) defect reproduced on main head at submission moment** [MEASURED, v5.5 A/B on pristine `3f2fe7df`, rustc 1.99.0, same command ± env flag]:
  - `RUSTFLAGS='' CARGO_TARGET_DIR=<ext> cargo test --release -p ginux-vfs-index --test overflow_checks_release` (no flag) → **FAILED**, exit 101, literal: `note: test did not panic as expected at crates/ginux-vfs-index/tests/overflow_checks_release.rs:16:4`.
  - same + `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` → **ok. 1 passed**, exit 0.
  - Local run reproduced both directions; **Actions re-run with the final command COMPLETED (run 42195146548, 09:27Z): C1 exit 101, C2 exit 0, C3 exit 0 on ubuntu-24.04; C1=101/C2=0 on macOS arm64 too.**
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
> Measured at SHA 3f2fe7df (latest completed probe run, ubuntu-24.04): `make test-unit` 65/65 with the flag (and baseline) on ubuntu-24.04 and macOS arm64; `ginux` 122,720 → 122,680 bytes (−40; cause not established); `ginux-vfs-index` +1,608 (+0.46%); scan timing median 203.0 → 200.1 ms (ranges 201.7–205.9 / 198.2–202.7, overlapping; 12 alternating pairs). Rocky VM targets were not exercised. Numbers, variance, limits: https://github.com/hafid-logic/ginux-watch/blob/4b73834650847e39b58996a4c05368fd791b4ace/inbox/evidence/2026-11-06-222-evidence/03-release-runtime-cost.md. Prepared with AI assistance, reviewed by me.

## Conflict + duplication notes for the reviewer (Abdelhafid)

- v5.5 resolved the old `RUSTFLAGS='-C linker=cc'` concern by measurement: the unified `RUSTFLAGS=''` command links and discriminates with `.cargo/config.toml` untouched (A/B above); the Actions re-run with the final command completed on the runner (run 42195146548: C1=101/C2=0/C3=0).
- Separate follow-up item (not in this PR): wire `test-release-overflow` into the CI job's run list — a ≤3-line addition, proposable once this lands.
- If you prefer no Makefile touch at all, drop hunk 2; the test still runs via the documented cargo invocation. (Directive asked to state the CI cost explicitly: it is 2 lines.)
- v5.6 additions for the reviewer: the v5.5 re-run completed AFTER the v5.5 delivery (run 42195146548) — its numbers are appended to evidence memo 03; the PR body now quotes the latest completed run (same-run A/B valid). Separate v5.6 finding, NOT part of this PR: the #207 harness detector was recalibrated (old ~18% divergence figures were a stdin-contamination artifact; corrected numbers + controls in memo 04). No upstream text mentions the old figures.
- Circuit-breaker check before publish (re-verified live in session 42, ~11:0xZ, HTML): #222 comments = 2 (ours + owner reply 05:29:33Z, nothing after); #207 open, head `e7f5f552`, latest activity 2026-11-05, nothing after; re-check live immediately before posting. Upstream main still `3f2fe7df` with byte-identical Cargo.toml/Makefile (sha256-checked vs pinned copies this session).

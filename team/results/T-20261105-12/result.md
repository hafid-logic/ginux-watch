# T-20261105-12 — W2: upstream tests/CI @0e06a986 + our ginux-verify dispatch (v4.0 §3)

## خلاصة / Summary
- [MEASURED] Upstream main has pivoted away from the UEFI/UEFI-boot pipeline: at `0e06a986` (merge of PR #204, 2026-11-05T19:15:58Z, `repos/gmkurtzer/ginux/commits/0e06a986`) the Makefile builds Linux binaries (`x86_64-unknown-linux-gnu`) and `make test` gates run inside a **Rocky Linux 10.2 VM under QEMU** (evidence/upstream-Makefile, fetched 20:18:13Z). No OVMF/`x86_64-unknown-none`/`Boot test`/`GINUX_KERNEL_*` remain.
- [MEASURED] Our dispatch run **42102046103** on main: conclusion **failure** — both matrix jobs: `doctor=2 check=0 test=2`. `check` (cargo fmt+clippy) is green; `doctor` and `test` fail because main now requires a **Darwin-arm64 reference host**, `qemu-img`, `hdiutil`, docker helper image, and a cached Rocky host image (`missing Rocky host image; run make host-image-fetch` → `make: *** [Makefile:98: test-intercept] Error 2`). This red run is DATA about what main no longer contains / now requires — no fix attempted upstream.
- [MEASURED] Upstream CI (`.github/workflows/check.yml`) never runs QEMU/Rocky gates: PRs+pushes are validated by cargo static/unit checks (macos-15-intel) and native launch/process tests (ubuntu-24.04).
- [OBSERVED] No visible branch protection on upstream main (`repos/gmkurtzer/ginux/branches/main/protection` → HTTP 404, fetched 20:18Z).

## Dispatch evidence (our Actions)
- [MEASURED] Run URL: https://github.com/hafid-logic/ginux-watch/actions/runs/42102046103 — id `42102046103`, workflow `ginux-verify.yml`, ref main, `target=main`, `qemu_versions=["10.0.13","10.1.2"]`, event workflow_dispatch, createdAt 2026-11-05T20:17:45Z, status completed, conclusion **failure** (retrieved 20:20:39Z via `gh run view`).
- [MEASURED] Per-job conclusions (`gh run view --json jobs`): `discover => success`; `verify (main, 10.1.2) => failure` (20:17:55Z→20:18:36Z); `verify (main, 10.0.13) => failure` (20:17:55Z→20:20:16Z).
- [MEASURED] Status line per job (`doctor, check, test` step): `doctor=2 check=0 test=2` on **both** QEMU versions (evidence/run-42102046103-full.log, downloaded 20:20:51Z).
- [MEASURED] Note: the two jobs checked out **different upstream SHAs** — 10.1.2 job: `upstream_sha=0e06a9860250b655a094761cd424bc022fd8db68`; 10.0.13 job: `upstream_sha=26609015771e9b8a3cb328857a85495b0ab2261b` — because main moved mid-run (PR #206 merged ~20:18Z). Both SHAs show the same result.
- [MEASURED] Failure essence (job 10.1.2, log lines 20:18:15–20:18:33Z): `doctor: qemu-img MISSING`, `doctor: hdiutil MISSING`, `doctor: reference host unsupported (Linux-x86_64)`, `doctor: cached Rocky host absent (run make host-image-fetch)` → `make: *** [Makefile:14: doctor] Error 1`; then `missing Rocky host image; run make host-image-fetch` → `make: *** [Makefile:98: test-intercept] Error 2`. `test-unit` itself passed (28× `test result: ok`, 0 failed).
- [MEASURED] Artifacts: `logs-main-qemu-10.0.13` (5452 B), `logs-main-qemu-10.1.2` (5334 B) on run 42102046103.
- [MEASURED] Deviation (our repo only): first dispatch returned **HTTP 422** `(Line: 12, Col: 12): Unexpected value ''` — commit `78c864f` had left an empty `schedule:` key (only comments under it), which GitHub rejects at dispatch. Minimal fix: comment out the `schedule:` key too, commit `e918d29` (pushed 20:17Z). This is our-repo infra repair to enable the mandated dispatch, not an upstream fix.

## Upstream CI (check.yml @0e06a986)
- [MEASURED] Path `repos/gmkurtzer/ginux/contents/.github/workflows/check.yml?ref=0e06a986` (decoded, fetched 20:18:14Z; saved evidence/upstream-check.yml). Triggers: `on: pull_request` (all PRs) **and** `push: branches: [main]`. `permissions: contents: read`.
- [MEASURED] Job `static-and-unit` on `macos-15-intel`: `brew install ripgrep`; `rustup component add clippy rustfmt`; `rustup target add x86_64-unknown-linux-gnu`; `make check`; `make test-unit`.
- [MEASURED] Job `launch-integration` on `ubuntu-24.04`: `make build build-launch-fixture build-process-fixtures`; `sudo make test-launch`; `sudo make test-native-supervision`; `make test-process-native` — Python-driven native (non-QEMU) integration tests of process supervision/launch.
- [INFERRED] The Rocky/QEMU/`with-rocky-host.sh` gates are **developer-local** (doctor says "reference host macOS arm64"), not CI gates.

## Make targets @0e06a986 (evidence/upstream-Makefile, fetched 20:18:13Z)
- [MEASURED] Plain cargo/Rust (no VM): `check` (= `check-name` + `cargo fmt --check` + 14× `cargo clippy -D warnings`), `test-unit`, `test-cgroup`, `test-block`, `test-network` (cargo test filters), `build`, `build-process-fixtures`, `build-launch-fixture`, `clean`.
- [MEASURED] Native-Linux, no QEMU (need root for two): `test-launch`, `test-native-supervision`, `test-process-native` — exactly the set upstream CI runs on ubuntu-24.04.
- [MEASURED] Need Rocky host image + QEMU + ssh (TCG): `host-image-fetch/-verify`, `host-boot-test`, `test-intercept`, `test-runtime`, `test-config`, `test-domain`, `test-image`, `test-oci-image`, `test-oci-layers`, `test-devices`, `test-kernel-views`, `test-process`, `test-vfs`, `test-native-vfs`, `bench-baseline/-block/-network`, `demo-gate-1/3/4/5/6/7/8` (all via `with-rocky-host.sh` → `start-rocky-host.sh`: `qemu-system-x86_64 -machine q35 -accel tcg ...` + Rocky-10-GenericCloud qcow2 + SSH wait, fetched 20:18:58Z).
- [MEASURED] `doctor` itself now requires: 16 tools incl. `qemu-img`, `hdiutil`, `shasum`, `docker` + running Docker + pinned helper image + **host `Darwin-arm64`** + cached Rocky image (evidence/upstream-doctor.sh, fetched 20:18:48Z) — fails on any Linux runner.
- [MEASURED] `make test` = `check test-unit test-intercept test-runtime test-config test-domain test-image test-devices test-process test-kernel-views` — 7 of its 10 members are Rocky-gated; first Rocky target (`test-intercept`) aborts the chain (observed in run 42102046103).
- [MEASURED] The old target `reset-storage` no longer exists (absent from evidence/upstream-Makefile); our workflow's `make reset-storage` call is now a no-op failure that is ignored.
- [MEASURED] Old UEFI-era gates (OVMF boot, `Boot test passed/failed`, `GINUX_KERNEL_OK/PANIC`, virtio-net queue-size probes) are **gone from main** — zero matches in the full run log (evidence/run-42102046103-full.log).

## بوابات PR / How PRs are validated
- [OBSERVED] Branch protection API: `repos/gmkurtzer/ginux/branches/main/protection` → **404 Not Found** (fetched 20:18Z) → no protection visible to us.
- [MEASURED] In practice: check.yml runs on every PR (`on: pull_request`) and on every push to main; the two jobs cover cargo static/unit + native launch/process tests only (evidence/upstream-check.yml).
- [INFERRED] Merging is owner-discretion on green check.yml; the Rocky/QEMU suite is run manually by the maintainer (doctor's "reference host macOS arm64") and not enforced on contributors.
- [OBSERVED] Main moves fast: `repos/gmkurtzer/ginux/commits/main` = `26609015771e9b8a3cb328857a85495b0ab2261b` (PR #206) at fetch 20:18:04Z; `compare/0e06a986...main` → ahead_by 2, behind_by 0 (fetched ~20:19Z).

## بدون QEMU / What runs without QEMU (from their CI + Makefile)
- [MEASURED] `make check` + `make test-unit` — proven green on Linux x86_64 by our run 42102046103 (`check=0`) and by their macos job design.
- [MEASURED] `make build build-launch-fixture build-process-fixtures test-launch test-native-supervision test-process-native` — run by upstream CI on ubuntu-24.04 without QEMU (sudo needed for two).
- [MEASURED] `make test-cgroup test-block test-network` — plain cargo test filters.
- [MEASURED] NOT runnable without QEMU/Rocky: `make test` as a whole, and every `host-*`/`test-domain`/`test-vfs`/bench/`demo-gate-*` target.
- [INFERRED] Hypothesis — a future our-side CI gate for main: drop the OVMF/QEMU-boot verify job; keep `make check` + `make test-unit` + the three native launch/process targets as the green/red signal, and treat Rocky/QEMU gates as maintainer-local (report-only). Our ginux-verify should switch to `make check test-unit test-launch test-native-supervision test-process-native` (plus optional `doctor || true`), since `doctor`/`make test` are now structurally red on Linux runners.

## جدول أدلة / Evidence table
| # | Claim | Evidence | Fetched |
|---|---|---|---|
| 1 | Dispatch fixed + run created | run [MEASURED] id 42102046103, URL in dispatch section; fix commit `e918d29`; broken state from `78c864f`; 422 text verbatim above | 20:17:45Z |
| 2 | conclusion failure; jobs; timings | `gh run view 42102046103 -R hafid-logic/ginux-watch --json status,conclusion,jobs` | 20:20:39Z |
| 3 | doctor=2 check=0 test=2 (both jobs) | evidence/run-42102046103-full.log (lines `doctor=...`, 20:18:33Z / 20:20:12Z) | 20:20:51Z |
| 4 | two different upstream SHAs mid-run | same log (`upstream_sha=0e06a986…`, `upstream_sha=26609015…`) | 20:20:51Z |
| 5 | failure essence (missing Rocky image, doctor needs Darwin-arm64) | same log + evidence/upstream-doctor.sh @0e06a986 | 20:18:48Z |
| 6 | check.yml triggers+jobs @0e06a986 | evidence/upstream-check.yml (contents API ref=0e06a986) | 20:18:14Z |
| 7 | all make targets @0e06a986 | evidence/upstream-Makefile (contents API ref=0e06a986) | 20:18:13Z |
| 8 | Rocky/QEMU boot mechanics | evidence/upstream-with-rocky-host.sh, upstream-start-rocky-host.sh @0e06a986 | 20:18:58Z |
| 9 | no branch protection | API 404 `branches/main/protection` | 20:18Z |
| 10 | main HEAD moved 0e06a986→26609015 (PR #206) | `repos/gmkurtzer/ginux/commits/main`, `compare/0e06a986...main` | 20:18:04Z |
| 11 | artifacts logs-main-qemu-* | run 42102046103 artifacts API | 20:22Z |

No stop-and-report triggers: no reply/mention directed at our account, no security flaw observed in the fetched files, nothing requiring upstream publishing.

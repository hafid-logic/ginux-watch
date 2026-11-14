# C-3 — KVM feasibility: Ginux + a gate test on a GitHub Actions runner (دراسة الجدوى)

## 1) Verdict (الحكم)

**POSSIBLE (conditional) — and KVM is NOT the issue.** `make test-contract` itself is pure `cargo test` (no VM) and already runs on any hosted runner; the Rocky-VM gate tests (`host-boot-test`, `test-contract-runtime`) are **TCG-only by design** (upstream: "Acceleration: QEMU TCG only. KVM is not required or used" [MEASURED: docs/gate-1-foundation.md:20]; `-accel tcg,thread=multi` [MEASURED: scripts/start-rocky-host.sh:69]) — so the publicly documented absence of `/dev/kvm` on hosted ubuntu runners is **not** a blocker. The as-is blockers are two measured **non-KVM** macOS dependencies (doctor platform gate + `hdiutil` seed ISO), fixable with a small portability patch; after that, a TCG run fits a standard hosted-runner job budget [INFERRED: 15–25 min]. This matches the prior-session finding that run 42102046103 failed on ubuntu with `doctor=2 check=0 test=2` for exactly those non-KVM reasons.

## 2) Hard requirements table — [MEASURED file:line] unless tagged [INFERRED]

| Requirement | Value | Evidence (file:line) |
|---|---|---|
| Rocky image | `Rocky-10-GenericCloud-Base-10.2-20260525.0.x86_64.qcow2`, **544,997,376 bytes (~520 MiB)**, SHA-256 `9fc9e9ff…4b48`, from download.rockylinux.org | `config/rocky-host-image.env:1-5`, `config/rocky-host-image.CHECKSUM:1-2`; fetch: `scripts/fetch-rocky-host.sh:25` (curl --retry 3), `Makefile:18-19` |
| vCPUs | default **2** (`ROCKY_VCPUS`); multi-instance gate uses 4 | `scripts/start-rocky-host.sh:39`; `Makefile:195` |
| Memory | default **2048 MiB** (`ROCKY_MEMORY_MIB`); multi-instance gate 4096 | `scripts/start-rocky-host.sh:40`; `Makefile:195` |
| Acceleration | **TCG only**, q35, `-cpu max`, multi-thread; KVM explicitly not used | `scripts/start-rocky-host.sh:66-72`; `docs/gate-1-foundation.md:20,72-73`; `README.md:174-176` |
| Disk | base image ~520 MiB + qcow2 overlay (`build/rocky-host-overlay.qcow2`), persistent and reused across runs | `scripts/start-rocky-host.sh:55-63`; `scripts/rocky-host-common.sh:6-8` |
| Boot/readiness wall time | no number published upstream; script tolerates **120×5 s = 600 s** SSH wait + 12×5 s cloud-init retries | `scripts/start-rocky-host.sh:84-108` (bound MEASURED; actual boot time [INFERRED] 3–10 min on hosted runner) |
| Networking | user-mode slirp, `restrict=on` default, hostfwd `127.0.0.1:$ROCKY_SSH_PORT-:22` (22222 default; test suites isolate on 22408) — no privileged ports, no tun | `scripts/start-rocky-host.sh:81`; `scripts/rocky-host-common.sh:3`; `scripts/with-rocky-host.sh:5` |
| SSH steps | ed25519 key generated `build/cache/rocky/gate1_ed25519`; BatchMode ssh/scp wrappers to `ginux@127.0.0.1`; cloud-init user with NOPASSWD sudo | `scripts/rocky-host-common.sh:4-21`; `scripts/prepare-rocky-host.sh:11-36` |
| Seed ISO | built with **`hdiutil makehybrid` — macOS-only tool** | `scripts/prepare-rocky-host.sh:39-45` |
| doctor gate | requires `hdiutil` (macOS-only) among 15 tools; **hard-fails any platform except Darwin-arm64** | `scripts/doctor.sh:5,34-37` |
| Docker | required by doctor and by `instance-image-prepare` (pinned OCI helper image) feeding `test-contract-runtime` | `scripts/doctor.sh:22-32`; `Makefile:39-40,117-118` |
| Privileged / nested virt | none needed: TCG is pure userspace; ptrace SYSEMU works as ordinary process under TCG | `docs/gate-1-foundation.md:69-73` |
| Caching needs | `make clean` preserves the verified image cache; CI precedent: actions/cache for QEMU builds in our legacy verify | `docs/gate-1-foundation.md:25-26`; `.github/workflows/ginux-verify.yml:100-105` (watch repo) |
| Job-timeout precedent | legacy verify job: `timeout-minutes: 75`, inner `timeout 25m make test` | `.github/workflows/ginux-verify.yml:54,162` |
| Runner size | standard `ubuntu-24.04` hosted runner (4 vCPU / ~16 GiB) suffices for 2 vCPU / 2 GiB guest | [INFERRED] from GitHub documented runner specs + measured test-unit job (~10 s) in `reports/2026-11-06-runner-probe.md` |

## 3) Prior-session evidence (دليل الجلسات السابقة)

- `team/results/T-20261105-12/result.md` — [MEASURED] our dispatch run **42102046103** of upstream `make doctor/check/test` on ubuntu-24.04 (QEMU 10.0.13/10.1.2 built from source, TCG): **doctor=2 check=0 test=2**; doctor fails because main now requires a **Darwin-arm64 reference host, qemu-img, hdiutil, docker helper, cached Rocky image**; `make test` chain aborts at the first Rocky-gated target (`test-intercept`, "missing Rocky host image"). Raw log: `team/results/T-20261105-12/evidence/run-42102046103-full.log`.
- `reports/2026-11-06-runner-probe.md` — [MEASURED] on ubuntu-24.04: `make test-unit` **65/65 green, ~10 s, no Rocky VM**; launch-integration targets (test-launch, test-native-supervision, test-process-native) PASS ~21 s; `make check` fails only on missing ripgrep (`check-name.sh: rg: not found`) — `apt-get install ripgrep` fixes; macos-15/macos-26 arm64 also available for probes.
- `reports/feasibility-2026-11-05.md` — [MEASURED] the pure-Rust track (cargo-llvm-cov 88.6% lines over 10 crates, mutants, clippy) is green on CI — the non-VM gate tests are already hosted-runner-friendly.
- `docs/RECOVERY.md` §8 (line 70) — ginux-verify.yml: cron disabled 2026-11-05; **"on current main the gate needs Rocky-VM and will fail" (run 42102046103)**; dispatch-only.
- `HANDOFF.md` §2 (line 14) and §7 (line 60) — rustc absent in the local sandbox → heavy builds belong in Actions; disk-full lesson → heavy builds via Actions, not locally (supports running this on CI, not in the box).
- `STATE.md:49` (session 30) — verify default pinned to `bootable-kernel-final`; main failure 2/0/2 expected since PR #152 (main needs Rocky 10.2 VM).
- `.github/workflows/ginux-verify.yml:93-98,135` — KVM step is a **probe only** ("ls -l /dev/kvm || echo no /dev/kvm") and `QEMU_ACCEL=tcg` — we never relied on KVM.

## 4) Estimate if POSSIBLE / blocker chain (التقدير وسلسلة العوائق)

- **`make test-contract` (closest literal target)** — pure `cargo test -p ginux-contract -p ginux-instance` + `contract-doc --check` [MEASURED: `Makefile:113-115`]. Runs on `ubuntu-24.04` today; [INFERRED] 2–5 min cold. No VM, no KVM, no patch.
- **Rocky-VM gate tests** (`host-boot-test` = boot + `check-rocky-host.sh` [MEASURED: `Makefile:24-25`]; `test-contract-runtime` [MEASURED: `Makefile:117-118`]) — blocker chain on a hosted ubuntu runner:
  1. `make doctor` fails: platform gate Darwin-arm64-only + `hdiutil` missing [MEASURED: doctor.sh:5,34-37; run 42102046103].
  2. `prepare-rocky-host.sh` cannot build `build/rocky-seed.iso` on Linux (hdiutil-only) [MEASURED: prepare-rocky-host.sh:39-45].
  3. Rocky image must be fetched (network) or restored from cache; `instance-image-prepare` needs Docker + pinned helper image (available on ubuntu hosted runners).
  4. TCG boot cost [INFERRED] 3–10 min SSH + cloud-init (script bound 600 s [MEASURED]), then the tests themselves are a few ssh/scp invocations [INFERRED] <5 min.
- **Estimated job** (after a 2-line portability patch: genisoimage/xorriso for the seed ISO + doctor platform tolerance, `apt-get install qemu-system-x86 qemu-utils genisoimage ripgrep`): **~15–25 min** on standard `ubuntu-24.04` (4 vCPU/16 GiB), fits a 30–45 min timeout. Caching plan: `actions/cache` keyed by `ROCKY_IMAGE_SHA256` for `build/cache/rocky` (~520 MiB) + cargo cache; overlay disk fresh per run (correctness: tests must not share operator state — `with-rocky-host.sh:4-8` already isolates).
- **Risks**: TCG boot variance near the 600 s bound on loaded runners; `shasum` availability on minimal images (verify-rocky-host.sh:18 uses it; present on ubuntu via perl); no upstream green reference for VM targets in CI (upstream's own check.yml deliberately excludes them [MEASURED: .github/workflows/check.yml:11-74]); doctor bypass must not weaken its checksum verification.

## 5) What would change the verdict

- **If the flow hard-required KVM**, hosted-runner verdict would be NOT POSSIBLE (no `/dev/kvm` on ubuntu-latest, publicly documented) — but it does not: TCG-only is measured. (Decisive-blocker clause therefore not triggered.)
- Upgrades to **POSSIBLE as-is, no patch**: one measured workflow_dispatch probe on ubuntu showing TCG boot+gate completing in time — it would prove boot wall time within timeout; only doctor/hdiutil remain.
- **Self-hosted runner** (Linux, bare metal or with /dev/kvm): removes TCG-time risk entirely and makes `host-boot-test` cheap; also satisfies any future KVM-needing variant.
- Upstream adopting the seed-ISO/doctor portability (or a fork branch carrying it) removes the patch risk.
- macos-15-intel (upstream's static CI image) satisfies Darwin-arm64 + hdiutil for doctor/boot, but Docker daemon is not available on macOS hosted runners → `instance-image-prepare`-dependent gates stay blocked there [INFERRED].

## 6) Sources (المصادر)

- upstream clone `/home/z/my-project/work/upstream-ginux` (origin/main 285d025): `scripts/start-rocky-host.sh`, `scripts/check-rocky-host.sh`, `scripts/prepare-rocky-host.sh`, `scripts/fetch-rocky-host.sh`, `scripts/verify-rocky-host.sh`, `scripts/rocky-host-common.sh`, `scripts/with-rocky-host.sh`, `scripts/doctor.sh`, `scripts/test-contract-runtime.sh`, `scripts/test-cli.sh`, `scripts/fuzz-security.sh`, `scripts/test-host-lifecycle.sh`, `Makefile`, `README.md`, `AGENTS.md`, `config/rocky-host-image.env`, `config/rocky-host-image.CHECKSUM`, `docs/gate-1-foundation.md`, `docs/security-boundary.md`, `.github/workflows/check.yml`.
- watch repo `/home/z/my-project/work/ginux-watch`: `reports/feasibility-2026-11-05.md`, `reports/2026-11-06-runner-probe.md`, `reports/2026-11-05-reassessment.md:11`, `docs/RECOVERY.md:70,47`, `HANDOFF.md:14,60`, `STATE.md:49`, `directives/v8.0-20261114.md` (item C-3), `.github/workflows/ginux-verify.yml`, `team/results/T-20261105-12/result.md` + `evidence/run-42102046103-full.log`, `team/results/T-20261105-15/result.md`.
- Make targets found (gate tests): VM-free — `test-contract` (:113), `test-unit` (:120), `test-release-overflow` (:135), `test-cgroup` (:206), `test-block` (:209), `test-network` (:212), `test-cli` (:132), `test-oci-layers` (:57), `test-generic-oci` (:185), `test-gate15-report` (:303), `test-host-lifecycle` (:224), `test-bench-compare` (:294), `check-name`/`check-instance-terminology` (:81-85), `fuzz-security` (:253, bounded 5 s/target); Rocky-VM-gated — `host-boot-test` (:24), `test-contract-runtime` (:117), `test-intercept` (:138), `test-runtime` (:153), `test-config` (:156), `test-instance` (:159), `test-devices` (:169), `test-kernel-views` (:175), `test-systemd` (:179), `test-vfs` (:227), `test-native-vfs` (:230), plus aggregates `test-security` (:262), `test-recovery` (:271), `test` (:233) that include VM-gated members. Upstream `check.yml` runs only VM-free targets [MEASURED: .github/workflows/check.yml:25-73] — so yes, gate tests run without the Rocky VM in upstream CI (`check`, `test-unit`, `test-release-overflow`, `test-launch`, `test-native-supervision`, `test-process-native`, `test-gate1-setup`, `test-tracee-kill`).

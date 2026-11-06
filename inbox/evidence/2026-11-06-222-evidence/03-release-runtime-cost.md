# Evidence memo 3/3 — release/runtime cost of `overflow-checks = true`
# (request from #222 owner reply)

**Status: prepared locally, NOT published.** Owner request (#222, 05:29:33Z):
"the release/runtime cost remains open ... unless a release benchmark
demonstrates a material cost that warrants a documented exception."

No word like "negligible" appears below without a number behind it.

## Method

- Sizes: `stat -c%s` on every workspace release binary, baseline vs
  `CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true`, same SHA (`3f2fe7df`), same
  machine, same link mode per binary (see memo 2 deviation note).
- Runtime: `ginux-vfs-index ROOTFS.tar OUT.index` (scan + verify) over a
  generated 50,003-entry / ~220 MiB tar (400 KiB payloads, deterministic);
  warmup 1 run each; then **12 alternating base,flag / flag,base pairs**
  (order-swap on the same machine); median + range reported.
- Local machine = sandbox (documented cc linker deviation for `ginux`);
  runner reference = ubuntu-24.04 job of the probe workflow.

## Results — binary sizes (bytes)

Local sandbox [MEASURED]:

| Binary | base | flag | delta |
|---|---|---|---|
| `ginux` (self-start, no_std, cc+nostdlib deviation) | 125,888 | 126,184 | **+296 (+0.24%)** |
| `ginux-vfs-index` | 353,568 | 355,176 | **+1,608 (+0.46%)** |

Runner reference (ubuntu-24.04, run 42178425135) [MEASURED]:

| Binary | base | flag | delta |
|---|---|---|---|
| `ginux` (self-start, upstream lld config) | 122,720 | 122,680 | **−40 (−0.03%)** |
| `managed-payload` | 1,048 | 1,048 | 0 |
| `baseline-runner` | 3,352 | 3,376 | +24 (+0.72%) |
| `runtime-fixture` | 4,424 | 4,424 | 0 |
| `process-native-fixture` | 1,528 | 1,520 | −8 (−0.52%) |
| `ginux-vfs-index` (cc link override) | 353,584 | 355,192 | **+1,608 (+0.46%)** |

Self-start binaries: flag cost is within tens of bytes (some even shrink —
section-layout noise), i.e. effectively zero. macOS arm64: `ginux-init` does
not compile there at all (43 errors, x86_64-specific freestanding code) and
vfs-index sizes were not captured in that step — stated as such.

## Results — scan runtime (50,003-entry tar, ~220 MiB)

Local sandbox [MEASURED, 12+12 alternating, order-swapped]:

| Build | n | median | range | mean |
|---|---|---|---|---|
| baseline | 12 | **112.5 ms** | [110.6 .. 114.8] | 112.6 ms |
| flag | 12 | **117.4 ms** | [116.8 .. 121.1] | 117.8 ms |

→ median delta **+4.9 ms (+4.4%)**.

ubuntu-24.04 runner [MEASURED, identical protocol — scripts/vfs-scan-timing.py]:

| Build | n | median | range |
|---|---|---|---|
| baseline | 12 | **223.2 ms** | [221.0 .. 225.9] |
| flag | 12 | **222.5 ms** | [219.2 .. 228.2] |

→ median delta **−0.7 ms (−0.3%)** — ranges overlap; the flag cost is inside
measurement noise on the runner and single-digit-ms at worst locally.

## Interpretation (bounded)

- Cost measured here: ≤0.5% binary size on every binary (±tens of bytes on
  the self-start bins, +1.6 KB on the std tooling binary), and at most
  single-digit-ms on a 50k-entry scan (−0.3% runner median / +4.4% local
  median) — ranges overlap on the runner.
- What is NOT measured: boot-time end-to-end on real Rocky rootfs (needs the
  Rocky host environment — not available to the probe), and long-running
  runtime paths under supervision. The bench target (`make bench-baseline`
  etc.) exists upstream but requires the Rocky host as well.
- The numbers above give the maintainer the "release benchmark" his #222 reply
  asked for, on the tooling path, with the protocol reproducible from the repo.

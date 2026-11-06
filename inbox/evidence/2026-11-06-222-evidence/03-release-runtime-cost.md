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

Runner reference (ubuntu-24.04) [MEASURED — probe run]: see run log table
(self-start bins under upstream lld config; vfs-index under cc override).
macOS arm64 (macos-15) sizes: see run log.

## Results — scan runtime (50,003-entry tar, ~220 MiB)

Local sandbox [MEASURED, 12+12 alternating, order-swapped]:

| Build | n | median | range | mean |
|---|---|---|---|---|
| baseline | 12 | **112.5 ms** | [110.6 .. 114.8] | 112.6 ms |
| flag | 12 | **117.4 ms** | [116.8 .. 121.1] | 117.8 ms |

**Median delta: +4.9 ms (+4.4% of baseline median)** for a full
scan+verify pass over 50k entries. Runner reference: see run log
(same protocol, same script — scripts/vfs-scan-timing.py).

## Interpretation (bounded)

- Cost measured here: ~0.2–0.5% binary size, ~4–5% on a header-bound scan of
  50k entries (the scan reads headers, not payload bytes, so this is close to
  the arithmetic-check overhead upper bound for this tool).
- What is NOT measured: boot-time end-to-end on real Rocky rootfs (needs the
  Rocky host environment — not available to the probe), and long-running
  runtime paths under supervision. The bench target (`make bench-baseline`
  etc.) exists upstream but requires the Rocky host as well.
- The numbers above give the maintainer the "release benchmark" his #222 reply
  asked for, on the tooling path, with the protocol reproducible from the repo.

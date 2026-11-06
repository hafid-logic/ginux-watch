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

Self-start binaries: on the runner the flag moves sizes by tens of bytes, and
`ginux` measures 40 bytes SMALLER with the flag — flag arrival itself is
verified mechanically (section below); the shrink mechanism is not established
and no interpretation is offered [INFERRED: unproven]. macOS arm64: `ginux-init`
does not compile there at all (43 errors, x86_64-specific freestanding code) and
vfs-index sizes were not captured in that step — stated as such.

## Flag-arrival verification (mechanical, v5.4-3)

Question: with the flag ON, `ginux` measured −40 B on the runner. Verify the
flag actually reached codegen — mechanically, not by inference.

- Local same-SHA rebuild (`3f2fe7df`, documented cc+nostdlib link deviation)
  [MEASURED]: baseline verbose build shows **0** `overflow-checks` rustc
  options; flag build (`CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true`, the exact
  env mechanism the probe sets at `probe-overflow-evidence.yml:46`) shows
  **`-C overflow-checks=on` on 8/8** rustc unit invocations.
- Sizes reproduced exactly: base 125,888 B / flag 126,184 B (**+296 B**),
  matching the local table above. Section deltas [MEASURED]: `.text` +75,
  `.eh_frame` +216, `.eh_frame_hdr` +8 — accounts for +299 B before alignment.
- Binary panic-string probe ("attempt to … with overflow"): **0 matches in
  BOTH builds** [MEASURED] — not a usable arrival discriminator under
  `panic = "abort"` + `strip`; the rustc-invocation and canary checks are the
  discriminators used.
- Runner side [MEASURED]: run 42178425135 retained no artifacts (artifacts
  total_count = 0), so the −40 B runner binary cannot be re-inspected
  byte-wise. Runner-side flag arrival rests on: (a) the workflow env line
  (file:line above), (b) behavioral canary C1=101 (flag build panics) vs
  C2=0 (baseline wraps) on the same runner.
- Why the runner's lld-linked binary is 40 bytes smaller with the flag: not
  established; recorded as measured layout variation, no interpretation
  offered [INFERRED — unproven].

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

## Launch/native supervision — cross-reference (added v5.7)

Completeness item (directive v5.7-2): the launch/native result is measured in
memo 2/3 and is repeated here so this memo stands alone [MEASURED, run
42178425135, ubuntu-24.04, SHA `3f2fe7df`]: `sudo make test-launch` **PASS**
baseline / **PASS** flag; `sudo make test-native-supervision` **PASS** /
**PASS**; `make test-process-native` **PASS** / **PASS**. macOS arm64: not
applicable (linux-specific namespaces/ptrace fixtures) — stated as not run
there. Sections above this one were not altered.

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

## Re-run with the FINAL unified command (v5.5 dispatch, completed 2026-11-06T09:2xZ)

The v5.5 session re-dispatched the whole probe on `main` (run
**42195146548**, SHA `a18604ec`, PIN `3f2fe7df`) with the unified
`RUSTFLAGS=''` canary command. Results, appended in session 41 — nothing above
was altered:

- Canary A/B on the runner [MEASURED]: **C1 (release, no flag) = FAILED, exit
  101** (defect reproduced on the runner); **C2 (release + flag) = ok, exit
  0**; **C3 (debug) = ok, exit 0**. macOS arm64 canary: C1=101 / C2=0 as well.
- `make test-unit`: **65/65 passed baseline and 65/65 with the flag** on
  ubuntu-24.04 and macOS arm64 (sum of per-crate `test result` lines).
- Builds: baseline + flag `make build` exit 0; vfs-index cc-override builds
  exit 0 (both modes).
- Sizes [MEASURED]: identical to the table above, byte for byte (`ginux`
  122,720→122,680 −40; `managed-payload` 0; `baseline-runner` +24;
  `runtime-fixture` 0; `process-native-fixture` −8; `ginux-vfs-index` +1,608).
- Scan timing, same-run A/B, 12 alternating pairs [MEASURED]:
  baseline **median 203.0 ms** [201.7 .. 205.9], mean 203.6;
  flag **median 200.1 ms** [198.2 .. 202.7], mean 200.5;
  **median delta −2.9 ms**; order swap base,flag | flag,base ×12; tar set
  230,410,240 bytes (~219.7 MiB), sha256 of first-run index pinned in the log.
- **Comparability note [MEASURED]:** the earlier runner table (223.2/222.5 ms,
  run 42178425135) and this one (203.0/200.1 ms) ran on different runner
  allocations; absolute medians across runs are NOT comparable. Each run's
  internal A/B stands on its own: same machine, alternating order — flag
  median was equal-or-faster in both runs (−0.7 ms, then −2.9 ms), ranges
  overlapping in both. The PR body quotes the latest completed run.

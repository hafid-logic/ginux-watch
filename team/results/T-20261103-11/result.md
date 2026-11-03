# T-20261103-11 — Verification of feature/fuzz-targets (v2.8 §3) [DONE]

Run: https://github.com/hafid-logic/ginux-watch/actions/runs/41614443506
(dispatch-only `fuzz-branch-verify.yml`, `contents: read`, untrusted-code checkout
without credentials; fork branch `hafid-logic/ginux@feature/fuzz-targets` @ `eccb0de7`).
Run history: run1 41598621579 (check=2/test=2 — missing `rustup target add
x86_64-unknown-none`, workflow bug, not PR content), run2 41599090806 (7/7 SUCCESS;
coverage errored "corpus does not contain program-input files"), run3 41602622460
(profdata merged, no lcov), run4 41605014987 (llvm-cov loaded the non-instrumented
run binary → "no coverage data found"), run5 41614443506 = **final, 7/7 SUCCESS**.

## 3a — upstream checks with fuzz/ present [MEASURED, run5 job "upstream-checks"]
`make doctor` = 0, `make check` = 0, `make architecture-check` = 0, `make test` = 0
(QEMU 10.1.2 TCG) on branch sha `eccb0de7`. fuzz/ is invisible to root
workspace/check scripts (card T-20261103-06: 17 explicit workspace members,
per-package clippy list, enumerated-file architecture checks).

## 3b — documented smoke (README commands, verbatim) [MEASURED, run5]
`fuzz-smoke` ×3 SUCCESS: all targets exit 0, zero crash/oom/timeout/leak artifacts.
Seeds loaded per round logs: 53 (70,650b) + 34 (3,110b) + 26 (10,063b).

## 3b — 10-minute rounds [MEASURED, run5 `fuzz-round` ×3, 601 s each]
| target | execs | regions | functions | lines | crashes |
|---|---|---|---|---|---|
| oci_surfaces | 24,918,248 | 92.95% | 97.94% | 96.87% | 0 |
| protocol_surfaces | 101,564,909 | 97.50% | 100.00% | 97.37% | 0 |
| volume_surfaces | 46,269,525 | 99.43% | 100.00% | 100.00% | 0 |
| **total** | **172,752,682** | — | — | — | **0** |

Coverage raw TOTAL rows (llvm-cov report -summary-only; columns re-derived from raw
values: regions=(851-60)/851, functions=(97-2)/97, lines=(670-21)/670, (200-5)/200,
(152-4)/152, (174-1)/174): evidence `coverage-*.log` in this directory.
NOTE: `coverage-summary-*.txt` labels its third column "functions" — that column is
branches (none in these crates); real functions% = 97.94/100/100.
Consistency cross-check vs historical measured runs (reports/2026-11-03.md §12-§13,
different environment): oci 92.95 vs 93.18 regions (10-min round vs 3x560s),
protocol 97.50 identical, volume 99.43 identical [MEASURED].

## 3c — numbers cited on #58 have log-backed sources [MEASURED]
41.0M = 41,000,918 (reports/2026-11-03.md:110), 247.1M = 247,112,565 (:116),
15.3M = 15,272,896 (:133), 87.8M = 87,846,486 (:148). The PR cites only run5
numbers + these sourced historicals (via #58). No unsourced numbers.

## CI decision input (2e) [MEASURED]
Upstream HAS `.github/workflows/` at c86945b1 (check.yml + issue-14-linux-repro.yml;
check.yml push-trigger blob corrupted `branches: ain]` — record-only per D11
precedent). Decision: NO CI workflow in the PR (upstream maintains its own minimal
CI; the maintainer's #58 reply did not request fuzz CI; README smoke reproduces
anywhere). Reason documented in the PR text.

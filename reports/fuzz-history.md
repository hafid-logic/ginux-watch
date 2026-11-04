# fuzz-history (v3.2 §1)

One row per target per round. Columns: date (UTC) | trigger | upstream main head
| target | seconds | execs | cov regions % | cov lines % | cov functions % |
crash artifacts | run url.
Column note (carried from run5 recipe): the last coverage column is named
'functions' by llvm-cov TOTAL row field 13 but behaved as branch coverage in
prior sessions — read comparatively, not absolutely.

| date | trigger | head | target | seconds | execs | cov regions | cov lines | cov functions | crashes | run |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | oci_surfaces | 1200 | 70649687 | 93.54% | 97.31% | - | 1 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | protocol_surfaces | 1200 | 252674296 | 97.50% | 97.37% | - | 1 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | volume_surfaces | 1200 | 97633959 | 99.43% | 100.00% | - | 1 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |

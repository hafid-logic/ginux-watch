# fuzz-history (v3.2 §1)

One row per target per round. Columns: date (UTC) | trigger | upstream main head
| target | seconds | execs | cov regions % | cov lines % | cov functions % |
crash artifacts | run url.
Column note (carried from run5 recipe): the last coverage column is named
'functions' by llvm-cov TOTAL row field 13 but behaved as branch coverage in
prior sessions — read comparatively, not absolutely.

| date | trigger | head | target | seconds | execs | cov regions | cov lines | cov functions | crashes | run |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | oci_surfaces | 1200 | 70649687 | 93.54% | 97.31% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | protocol_surfaces | 1200 | 252674296 | 97.50% | 97.37% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |
| 2026-11-04T04:25:02Z | workflow_dispatch | c8d12653 | volume_surfaces | 1200 | 97633959 | 99.43% | 100.00% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41770788551 |

> تصحيح 2026-11-04 (جلسة 24): صفوف run 41770788551 سُجلت `crashes=1` خطأً — عدّاد `ls artifacts/`
> أحصى مجلد cargo-fuzz الذاتي الفارغ (artifacts/<target>/). الدليل: «Done ... runs» وخروج 0 ولا أسطر
> ERROR/crash في السجلات؛ صفر ملفات crash-*/oom-*/timeout-*/leak-*. العدّاد أُصلح في fuzz.yml.
| 2026-11-04T17:50:00Z | parser-crate-touched c8d12653..f45f1e4f | f45f1e4f | oci_surfaces | 600 | 26648962 | 93.31% | 97.31% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41879122802 |
| 2026-11-04T17:50:00Z | parser-crate-touched c8d12653..f45f1e4f | f45f1e4f | protocol_surfaces | 600 | 160579926 | 97.50% | 97.37% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41879122802 |
| 2026-11-04T17:50:00Z | parser-crate-touched c8d12653..f45f1e4f | f45f1e4f | volume_surfaces | 600 | 87912787 | 99.43% | 100.00% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/41879122802 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | audit | 1800 | 9984069 | 2.04% | 2.06% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | config | 1800 | 9934253 | 5.00% | 5.67% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | device | 1800 | 9717190 | 2.21% | 2.04% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | elf | 1800 | 5990435 | 1.62% | 1.58% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | kernel-path | 1800 | 7785403 | 1.76% | 1.65% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | selector | 1800 | 10236563 | 2.81% | 2.66% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | syscall | 1800 | 5284997 | 2.61% | 2.68% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |
| 2026-11-13T12:33:36Z | workflow_dispatch (v7.7-B2: Gate 13 targets >=30min/target) | 49b42307 | vfs-index | 1800 | 9841025 | 1.69% | 1.57% | - | 0 | https://github.com/hafid-logic/ginux-watch/actions/runs/43421884560 |

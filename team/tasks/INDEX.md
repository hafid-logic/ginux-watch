# Task index — contribution pipeline (v9.2)

Read `docs/PIPELINE-PLAYBOOK.md` first. Cap: 3 open upstream PRs; preparation uncapped.
Target inventory: 3 pushed + 3 nominated.
Harvest 2026-11-25: mutation-scan #1-#5 -> 176 survivors (state/discoveries.json); 3 new cards promoted.

## DONE
- 7 upstream PRs merged: #227 #295 #296 #310 #317 #319 #320
- open-PR cap raised 2 -> 3 (POLICY/AGENTS/authorization, commit 21322ab)
- `mutation-scan.yml` dispatchable cargo-mutants workflow merged (PR #72)
- `docs/PIPELINE-PLAYBOOK.md` — method, quality gate, 12 operational discoveries

## IN FLIGHT
- `tests/kernel-views-procfs-identity @ 73320a50` — pushed, opened upstream (21 lines, 3 mutants)
- T-20261125-scan-artifacts — runs green, harvest pending

## READY TO BUILD (measured survivors, screened for value)
- T-20261125-sysfs-device-kind      (isolation: cross-kind device data)
- T-20261125-cgroup-limits          (confinement: resource limit parsing)
- T-20261125-cgroup-controllers     (confinement: subtree_control parsing)
- T-20261125-identityfs-ns-pid      (identity: namespace pid link)
- T-20261125-devices-views-read-isolation (isolation: cross-instance device data)
- T-20261125-process-pipespace-lifecycle  (confinement: pipe end lifecycle)
- T-20261125-vfs-overlay-open-isolation   (access: overlay layer serving)

## BLOCKED
- T-20261125-dispatch-permission — needs App `actions: write` (UI dispatch works today)

## REJECTED (do not retry)
- allocator c_char — fixed upstream; also overlaps contributor PR #313
- blanket `RUSTFLAGS=''` in Makefile — breaks freestanding builds (rc=101 vs rc=0)
- `make check` / `test-contract` local failures — environment, owner CI is green
- `test-devices` / `test-kernel-views` / `test-vfs` full targets — require Rocky VM
- display/format mutants (init name rendering, human_size) — out of scope by policy

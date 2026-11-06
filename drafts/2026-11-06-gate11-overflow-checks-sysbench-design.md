# Gate 11 — overflow-checks impact on matched sysbench (DESIGN ONLY)

**Created:** 2026-11-06T20:4xZ (session 46, v6.3-5)
**Status:** DESIGN ONLY — do NOT run before Gate 11 officially starts (v6.3-5)
**Links:** PR #227 (`restore-overflow-checks`, head `9ac0f544`), Gate 11 spec `hdae/gates-todo/11-performance-characterization.md` @ upstream/main `8a475e8b`, prior evidence memos 03/04 @ `4b738346`

## Question this design answers

Does `overflow-checks = true` in `[profile.release]` (our PR #227 change)
push any mandatory Gate 11 sysbench workload beyond the **4% unfavorable
tolerance** vs the same binary built without the flag?

## Mapping to Gate 11's literal criteria (from the gate doc)

- Native/Rocky = 1.00x primary control; here the A/B control is the SAME
  ginux binary with vs without the flag — a strict subset of the gate's
  matched-protocol requirement, so results transfer.
- Mandatory rows: sysbench **cpu / memory / threads / mutex** at **1, 2, 4
  vCPU** where parallelism applies, **single-thread control retained at
  every allocation**.
- Per-row pass/fail at **≤ +4% in the unfavorable direction** (throughput
  −4% or latency/elapsed +4%); **no aggregate score may conceal a failing
  row**; exceptions only by recorded human decision.
- Report must show per row: native(control) value, Ginux value, ratio,
  percentage difference, variance, pass/fail — reproducible environment
  metadata (host kernel, ginux commit, image identity, contract, warmup,
  repetitions, raw numbers).

## Matched protocol (A/B, same host session)

1. **Environment:** one Rocky QEMU host session (TCG per upstream's dev
   env), matched CPU affinity and memory limits for both arms; warmup ≥ 2
   full runs before measurement; ≥ 10 measured repetitions per cell;
   report median + IQR.
2. **Arms:** A = release build, `[profile.release]` as upstream main has it
   (no overflow-checks); B = identical tree + our one-line
   `overflow-checks = true`. Byte-verify both binaries' rustc invocation
   flags (provenance method of memo 03: env line present 8/8 units).
3. **sysbench:** one pinned build, identical arguments both arms, run
   INSIDE a ginux domain (same contract) so mediation cost is constant and
   the delta isolates the overflow-checks codegen cost.
4. **Cells:** {cpu, memory, threads, mutex} × {1, 2, 4 vCPU} × {A, B} = 24
   rows minimum; every row individually judged at 4%; variance reported per
   row.
5. **Regression guard:** arm B vs arm A deltas are also stored as the
   versioned baseline for future Gate 11 runs (per the gate's
   "regressions against last accepted result" clause).

## Prior evidence we already hold (no rerun needed for context)

- Binary size: 125,888 → 126,184 bytes (+296B), `.text` +75B [MEASURED,
  memo 03 @ 4b738346].
- Launch/native supervision workloads: +4.9 ms (+4.4% worst-case local),
  runner medians 222.5 → 223.2 ms (medians overlap) [MEASURED].
- Canary C1=101 / C2=0 / C3=0 [MEASURED, runner] — correctness preserved.
- NOTE: the 4.4% local worst-case is on the 220 MiB archive scan, NOT a
  sysbench workload; it does NOT automatically violate Gate 11, whose rows
  are sysbench cpu/memory/threads/mutex. The sysbench matrix above is the
  gate-shaped answer.

## Risks / known unknowns

- TCG (no KVM) amplifies interpreter loops; overflow checks in
  ginux-vfs-index hot loops (scan_tar/parse_pax) may show up in file-heavy
  workloads — memory/threads/mutex rows likely insensitive; cpu row is the
  risk cell.
- If any row exceeds +4%: per Gate 11, that row FAILS and requires
  profiling + an optimization attempt (e.g., `#[inline(never)]` isolation,
  checked_sub rewrites in the three named sites) — NOT a silent threshold
  change; any exception needs the maintainer's recorded human decision.

## Execution gate

- Run ONLY after Gate 11 officially starts (its "Completed work" leaves
  "None; gate not started" today).
- Heavy runs belong in GitHub Actions per METHODOLOGY rule 9 (dispatch +
  `gh run watch`), not the local sandbox.
- No publishing of this design or its results upstream without
  Abdelhafid's explicit approved text (fixed rules; counter 1/1).

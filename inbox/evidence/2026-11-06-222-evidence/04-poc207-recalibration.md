# Evidence memo 4/4 — poc207 detector recalibration (v5.6): the v5.3/v5.4 T1/T3 divergence counts are INVALIDATED as magnitudes; strict divergence re-established with controls

**Status: prepared locally, NOT published.** Directive v5.6 items 1–3.
Supersedes the detection criterion of `poc/poc207_t123.c` (v5.3-5). Nothing
earlier is deleted anywhere — this memo records the invalidation and the
replacement measurement.

## The flaw (old criterion)

The v5.3-5 harness counted a divergence at poll-exit when
`snapshot_fd<=2 && revents != 0 && fd_post > 2` on slot 1. `revents != 0`
cannot distinguish "kernel polled the sentinel" from "kernel polled fd 0 and
fd 0 answered" (POLLIN from a ready stdin, or POLLNVAL/POLLHUP from a closed /
writer-less stdin) — followed by a sibling flip before the exit-stop read that
supplies `fd_post > 2` without any divergence. The traced process inherited
the launcher's stdin; on CI runners that is whatever the runner step had.

## Task 1 — hypothesis test (OLD harness, T1, 1,000,000 polls each, one sandbox machine) [MEASURED]

| tracee fd 0 (readlink /proc/<pid>/fd/0) | T1 hits / 1M |
|---|---|
| `/dev/null` (POLLIN always) | **283,621** |
| closed (readlink: none; POLLNVAL always) | **295,156** and **286,149** |
| pipe with open writer, no data (revents==0 guaranteed) | **1,145** and **1,046** |

Same machine, same code, only fd 0 changed: the old criterion inflates by
~250× when stdin is `/dev/null` or closed. Old-criterion T3 with a clean
pipe stdin measured 1,550/1M — the same inflated-criterion structure.

Runner old-criterion re-run the same morning (run 42195146548, 09:27Z,
PIN `3f2fe7df`) [MEASURED]: T1 **180,467**/1M, T3 **179,274**/1M — inside the
inflated band, far above the clean-pipe ~1k band.

**INVALIDATED [recorded per v5.6-3, nothing deleted]:** all v5.3/v5.4 T1/T3
counts (171,521 / 182,918 T1 and 171,223 / 178,994 T3 in runs 42177640755 /
42178425135; 180,467 / 179,274 in run 42195146548) are detector artifacts in
their majority and must not be cited as divergence rates. The structural
observation (snapshot validated fd 0, kernel executed poll on a different
descriptor) survives recalibration — see below.

## The fix (harness v5.6, commit 2f94954b)

- The tracee now creates its own fd 0: read end of an **empty pipe whose
  write end is held open** (parked at fd 9) — `poll(fd0)` returns
  `revents==0` deterministically, independent of how the harness was launched.
- Criteria: **T1** counts `snapshot==0 && revents==POLLNVAL` (fd 0 is open, so
  POLLNVAL can only mean the kernel copied a not-open value — the sentinel);
  **T3** counts `snapshot==0 && revents==POLLHUP` (fd 3 is a fifo read end;
  fd 0 cannot HUP). The `fd_post` exit-read is no longer evidence.
- Controls built in (no result without its control):
  **ctl_a** fds[1].fd fixed 0, gate active → expect zero nonzero revents;
  **ctl_b** fds[1].fd fixed sentinel, gate observe-only → expect POLLNVAL on
  100% of executed polls; **ctl_c** fds[1].fd fixed 3, observe-only → expect
  POLLHUP on 100%.
- Also fixed while recalibrating [MEASURED]: (a) the tracee never parsed the
  supervisor's argv — it always ran the default 1,000,000 iterations; the old
  runs passed 1,000,000 explicitly, so no old number changes because of this,
  but any smaller count silently measured 1M; (b) `gate_snapshot_sentinel`
  was never incremented (record-after-break bug) — now `gate_snapshot_invalid`
  and it matches `gate_denied` exactly; (c) a FIFO read end opened AFTER the
  writer's open+close reports NO revents at all (virgin-read-end state); the
  writer must be opened and closed while the reader is already held — ctl_c/T3
  setup now does the writer episode inside the tracee, after its own open.

## Task 3 — re-run on Actions, 2×1M + controls ×1M (run 42202168192, ubuntu-24.04, 10:22–10:26Z, PIN 3f2fe7df, harness 2f94954b) [MEASURED]

Controls first:

| control | result | verdict |
|---|---|---|
| ctl_a (fixed 0) | nonzero revents = 0 / 1,000,000 | PASS |
| ctl_b (fixed sentinel) | POLLNVAL = 1,000,000 / 1,000,000 (100.0000%) | PASS |
| ctl_c (fixed fifo fd 3) | POLLHUP = 1,000,000 / 1,000,000 (100.0000%) | PASS |

Measurements:

| run | polls | denied by gate | executed | hits | hits/executed | revents signature | T2 gate window med [min..max] |
|---|---|---|---|---|---|---|---|
| T1 (0↔sentinel) | 1,000,000 | 499,127 | 500,873 | **3,704** | 0.74% | POLLNVAL only (IN/ERR/other = 0) | 3,316 ns [2,305 .. 105,196] |
| T3 (0↔fifo fd3) | 1,000,000 | 498,829 | 501,171 | **3,091** | 0.62% | POLLHUP only (NVAL/IN/ERR = 0) | 3,266 ns [2,295 .. 52,367] |

Local sandbox reference (same harness, 1M each) [MEASURED]: T1 1,357
(0.27% of 500,081 executed), T3 1,260 (0.25% of 501,171); T2 med 2,391 /
2,381 ns; same clean signatures; controls PASS (200k each).

Runner fd 0 provenance (new step) [MEASURED]: `RUNNER_STEP_FD0=pipe:[15404]`
— the step shell's stdin is a pipe. The writer state of that pipe during the
invalidated runs was not logged, so which exact false-positive path fired on
the runner (POLLIN data vs writer-exit HUP) is not retroactively
determinable [INFERRED]; what is measured is that the old criterion produces
the runner-sized counts only when stdin is not quiet (sandbox table above).

## Conclusion (bounded)

- Strict divergence is RE-ESTABLISHED under the calibrated criteria with all
  three controls passing: in both 1M-poll runner runs the gate snapshot
  validated fd 0 while the kernel executed poll() on a not-open sentinel
  (T1: 3,704) or on a real fd 3 the snapshot never allowed (T3: 3,091). The
  proof threshold (≥1 in 1,000,000) is exceeded ~3,000×.
- The honest magnitude is ~0.6–0.7% of executed polls on the runner and
  ~0.25–0.27% locally — NOT the ~17–18% previously claimed. Rates are
  harness-specific [INFERRED to generalize no further]: the PTRACE_SYSCALL
  supervisor has a larger decision window than ginux's SYSEMU design
  (v5.3 note, unchanged).
- What remains INFERRED, unchanged from v5.4: whether a ginux tracee can ever
  actually hold fd > 2 (the fd-table invariant) — the harness proves the
  gate-vs-kernel race only, not reachability inside ginux.

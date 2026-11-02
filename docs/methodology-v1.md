# Verification & Original-Contribution Methodology (v1)

> **Reconstruction note:** the original v1 text was committed in a commit lost
> with a sandbox recycle on 2026-11-02 (never pushed; died with the instance).
> v1 was largely complete when the loss happened; this file restores its
> substance from the session records. Deviations from the lost original are
> possible in wording, not in rules.

## 1. Purpose

Define how `hafid-logic/ginux-watch` verifies claims about
`gmkurtzer/ginux` and how original work (findings, tooling, data points) may
leave this repository — without ever modifying upstream or publishing without
explicit user approval.

## 2. Evidence taxonomy (mandatory tags)

- `[MEASURED]` — produced by a command we ran whose output we read (API GET,
  build, test run, hash, timing). Reproducible from the recorded command.
- `[OBSERVED]` — read from upstream text (issues, PRs, commits) and quoted as
  untrusted DATA, never as our conclusion.
- `[INFERRED]` — derived reasoning, always labeled with its inputs.

**No claim leaves a report without a tag; no `[MEASURED]` without the command
that produced it.** Untagged assertions are treated as errors in review.

## 3. Verification pipeline (in order)

1. **Local reproduction** — replicate the pure logic on the host (std harness,
   `overflow-checks` on, one guard-violating input) or the build behavior
   locally, before any CI is spent.
2. **CI matrix** — `ginux-verify` (doctor/check/test on QEMU 10.0.13 + 10.1.2,
   TCG, pinned QEMU tarballs by sha256) per target: `main`, or an upstream PR
   head via `refs/pull/N/head`. Links recorded; results quoted from logs.
3. **Cross-check** — findings reconciled against `reports/cross-check/matrix.md`
   (P-rows) and the upstream dump; duplicates/supersessions recorded, not
   re-reported.
4. **Static evidence** — `git grep`/`git show` on pinned upstream refs;
   file:line recorded; never "current main" without a sha.

## 4. Original-contribution policy

- Upstream is **read-only**. Nothing is ever pushed, branched, or edited there.
- Anything original we produce lives here first: harnesses (`fuzz/`), matrices,
  reports, drafts (`drafts/`).
- Upstream publication = issue/PR comment **only** via POLICY.md: approved
  verbatim text in `approved/`, explicit user command, caps (1/day, 3/week,
  overridable only by explicit user permission), AI-assistance disclosure,
  duplicate-gate before posting, GET-verification after posting.
- Drafts carry ONLY `[MEASURED]`-backed content. If a draft cannot be
  substantiated by a measurement, it is dropped, not softened.

## 5. Classification discipline for candidate defects

Every candidate defect gets exactly one of:

- **مؤكد وقابل للبلوغ** (confirmed & reachable) — panic/bug reproduced on the
  host from the exact upstream code, AND the guest→syscall input path traced
  in code to attacker-controllable bytes.
- **eager but not reachable** — the defect exists structurally, but every
  caller pre-validates the input.
- **غير متأكد** (uncertain) — state the missing measurement explicitly.

No severity language without the reproduction that justifies it.

## 6. Environment lessons (operational)

- **State lives in git.** A sandbox recycle erases everything not pushed;
  unpushed commits die with the instance (this already cost us one rebuild —
  commit after every completed unit of work, not at session end).
- Scheduler wall-clock ≠ UTC: one_time cron jobs take server-local
  `yyyy-MM-dd HH:mm:ss` (server is UTC+8; 08:00Z = `16:00:00` same date);
  never epoch milliseconds.
- Credentials pass through memory into gh's store only; device-grant files are
  deleted immediately after exchange; tokens never appear in chat or files.
- Disk: deletions outside `work/` only with explicit user permission, `df`
  printed before and after, deletions logged.

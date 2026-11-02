# DRAFT — comment suggestion for gmkurtzer/ginux PR #54 (2026-11-02)

**STATUS: DRAFT ONLY — NOT PUBLISHED. POLICY: level 2 required (explicit user
permission). Weekly quota 2026-11-02 is 3/3 exhausted.**

Target: https://github.com/gmkurtzer/ginux/pull/54 (alternative: reply thread
on our own issue #43 — no upstream write needed there either).

Word count: 95. Backing evidence: 100% [MEASURED] (harness below + CI runs).

---

```text
Thanks for enabling release overflow-checks. Verifying head a0e9220b
(QEMU 10.0.13/10.1.2 TCG: doctor/check/test 0/0/0), a host
harness on verbatim upstream logic found five eager expressions that panic
under the new checks where release previously wrapped silently:

- linux_overlay.rs:539: `then_some(node.fifo_socket - 1)` evaluates the
  argument even when `fifo_socket == 0` — the first open of any named fifo
  underflows.
- cpu.rs:22504 (readlink), 23983 (execve), 25167 (openat), 37712 (mount):
  identical `byte - b'0'` folds — any byte < '0' after `/proc/self/fd/`
  (e.g. `/`) underflows.

Both print "attempt to subtract with overflow". Guards planned before merge?
(AI-assisted; details available.)
```

---

## Classification of the 5 sites (user directive 2026-11-02)

| # | Site | Eager? | Guest input path | Verdict |
|---|------|--------|------------------|---------|
| 1 | linux_overlay.rs:539 `fifo_socket()` | YES — `then_some` argument always evaluated | guest `mkfifo` → `create_fifo` (fifo_socket=0) → guest `open(fifo)` → `linux_openat` Fifo arm cpu.rs:25407-25408 → `linux_open_named_fifo` cpu.rs:31156 | **مؤكد وقابل للبلوغ** — first open of ANY named fifo panics under #54 |
| 2 | cpu.rs:22504 `linux_readlink_at` | YES (same fold) | guest `readlink("/proc/self/fd/1/")` — raw guest bytes, no gate before parse | **مؤكد وقابل للبلوغ** |
| 3 | cpu.rs:23983 child exec path resolve | YES (same fold) | guest child `execve("/proc/self/fd/<n>/")` (gated: LINUX_RUNTIME_MODE, pid≠1) | **مؤكد وقابل للبلوغ** (شرط وضعية Linux child) |
| 4 | cpu.rs:25167 `linux_openat` | YES (same fold) | guest `open("/proc/self/fd/1/")` | **مؤكد وقابل للبلوغ** |
| 5 | cpu.rs:37712 mount target resolve | YES (same fold) | privileged mount (euid 0 + ManageMounts) with target `/proc/self/fd/<n>/x` — trailing `/` stripped, internal `/` or `-` reaches the fold | **مؤكد وقابل للبلوغ** (شرط امتياز root) |

Trigger byte class: any byte 0x00–0x2F after the prefix (`/` = 0x2F, `-`, `.`,
space). Bytes ≥ '0' (e.g. `1x`) are SAFE — measured: fold returns None
correctly in both builds (initial static suspicion of silent mis-parse was
DISPROVEN by measurement).

## [MEASURED] evidence

1. Host harness (verbatim upstream bodies, std, rustc 1.99.1):
   `work/eager-proofs/harness.rs`
   - Build A (`-C overflow-checks=on`, PR #54 semantics): S1 input
     fifo_socket=0 → **PANIC "attempt to subtract with overflow"**; fold input
     `1/` → **PANIC**; input `-1` → **PANIC**.
   - Build B (`-C overflow-checks=off -O`, current-main release semantics):
     same inputs return normally (wrap discarded → None/ENOENT). No panic.
   - Both builds: `1x` → None; `12` → 12; fifo_socket=3 → Some(2).
2. CI (ginux-verify, TCG): run 41419158512 (target=54@a0e9220b) = 0/0/0 both
   QEMU versions, boot passed — the default suite never opens named fifos nor
   requests malformed `/proc/self/fd/` paths, so the gate test
   `release_profile_traps_size_overflow` (synthetic `usize::MAX + 1`) passes
   while the five real call sites remain unguarded.
3. Kernel impact context: panic=abort (F5) ⇒ guest-triggerable abort of the
   whole kernel under PR #54; same inputs are benign ENOENT on current main.

## QEMU runtime probe (optional per directive) — NOT PERFORMED

Reason: a live probe needs a guest ELF calling open/readlink on a malformed
`/proc/self/fd/` path (local kernel+QEMU+guest build ≈ 45 min, high
environment risk). Classification above rests on the computational proof plus
the traced syscall path (file:line recorded). If the user orders it, the probe
would boot 54@a0e9220b release via tests/qemu/boot.sh with a custom initrd —
upstream unmodified.

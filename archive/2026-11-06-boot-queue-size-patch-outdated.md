# boot-queue-size.patch — ARCHIVED AS OUTDATED (متقادم)

**Archived:** 2026-11-06T20:4xZ (session 46, v6.3-2)
**Original file:** `upload/boot-queue-size.patch` (1803 bytes, dated 2026-10-31, kept out of git — `upload/` untracked)
**Disposition:** OUTDATED — target file does not exist on upstream main head

## Why outdated (v6.3-2 rule applied)

The patch targets `tests/qemu/boot.sh`:

```
git cat-file -e upstream/main:tests/qemu/boot.sh
# => exit 128, "path 'tests/qemu/boot.sh' does not exist in 'upstream/main'"
```

- The whole `tests/qemu/` QEMU-boot harness was removed in the userspace
  transition (merge d337713b, #152, 2026-11-04) — ginux no longer ships that
  test path, and the current architecture (Rocky host + domain, Gate 9.5
  harnesses under `scripts/`) does not use it.
- Therefore the patch has **no apply target**: not a conflict, an absence.
  v5.2 evaluation (reproduced defect / test fails-before-passes-after) is
  moot without the file; only the secret/malware scan was performed
  (result: CLEAN — bash-only change, no network/eval/exfiltration, no
  credentials).
- Per v6.3-2: archived as outdated, **removed from the candidates list**.
  No push, no PR, no upstream comment.

## Permanent rule added (docs/METHODOLOGY.md rule 11)

Before evaluating ANY external patch: verify every target file exists on the
CURRENT upstream main head (`git cat-file -e upstream/main:<path>`). A patch
whose target was removed/restructured is outdated — archive it immediately
without a full v5.2 evaluation.

## Re-evaluation trigger

Only if upstream ever reintroduces a QEMU boot harness with the hardcoded
`queue size: 256` assertion AND the maintainer asks for portability help.
Until then this patch stays archived and out of every candidate list.

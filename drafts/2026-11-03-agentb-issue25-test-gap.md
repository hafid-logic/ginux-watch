# DRAFT — issue proposal (status: draft — لا نشر إلا باعتماد المستخدم حرفيًا)

بوابة التكرار: PASS على dump 18:21Z (لا بند قائم يقترح اختبار انحدار لـ#25/#49؛ تحفظ: البنود #77+ خارج dump — إعادة فحص عند توفر API قبل أي عرض).
المصدر: team/results/T-20261103-25/result.md (ب4) — فجوة مؤكدة [MEASURED: git diff 9e7e298^1..9e7e298 بلا اختبارات].

---

**Title:** Regression-test gap: SMP TLB shootdown (PR #49) has no failure-mode check

**Body (~120 words):**

PR #49 (merge 9e7e298) replaced a local `invlpg` with cross-vCPU TLB shootdown in `address_space.rs`. Reviewing the merged diff, we could not find a new regression test or boot-gate assertion that fails if the shootdown path is reverted to the local invalidation pattern — the existing SMP markers remain from earlier work.

Given `panic=abort` semantics and the single-host threat model discussed in #21/#22, a silent regression here would be hard to notice: the Rust compiler cannot catch it in safe code (our mutation experiments saw 0/30 seeded bugs in unsafe/C rejected by the compiler), and the default suite does not exercise SMP shootdown paths.

Would a boot-gate assertion be welcome — e.g. verifying that every active vCPU observes the address-space invalidation after `mprotect`-style operations?

Analysis assisted by AI, reviewed by Abdelhafid DJIDEL. Facts only; no security claim.

# مسودة نص مقترح — غير منشور، لا يُنشر إلا باعتماد المستخدم الحرفي (v4.0 §4)

الفرصة 2 من reports/2026-11-05-reassessment.md: استعادة `overflow-checks = true` في `[profile.release]`.
السياق: وُضعت أولًا في إطار تحقيقنا المنشور (#43 تحليل، #54 الإصلاح المدمج)؛ زالت أثرها في pivot الuserspace
(`[profile.release]` الحالي @0e06a986 = codegen-units/lto/opt-level/panic=abort/strip فقط).

---

**النص المقترح (issue أو PR، بالإنجليزية كما يفوق أسلوب المستودع):**

Title: `restore overflow-checks in release profile (lost in userspace pivot)`

Body (≤120 كلمة):
> During the standalone-kernel phase, `overflow-checks = true` was enabled in
> `[profile.release]` to make integer-overflow behavior deterministic in
> supervisor paths that validate untrusted input (see #43, #54). The current
> `[profile.release]` in the userspace tree no longer sets it, so release
> builds silently wrap on overflow again. The supervisor parses attacker-
> controlled structures (tar/PAX headers, volumes, configs) where a wrapping
> offset can turn into an out-of-bounds read/write downstream. Proposed
> one-line change:
>
> ```toml
> [profile.release]
> overflow-checks = true
> ```
>
> No benchmark has been run for this tree yet; happy to provide one for the
> parsing crates before merge, or send the change as a PR if preferred.

ملاحظات النشر (للمستخدم):
- قبل النشر: تأكد أن #54/#43 لا تزال تشير للأصل، وأن أحدًا لم يقدم نفس التغيير (فحص dump محدث).
- النسخة الأنسب: PR صغير (+1/−0) مع الإشارة إلى #43/#54 — يطابق نمط القبول السائد (fix ≤60 سطرًا، وسيط 39min).
- بديل إن ظهر تعارض: issue فقط، والPR بعد إشارة المالك.

# not-reported.md — مشاكل C غير المطروحة على upstream (مرتبة بالخطورة)

آخر فحص: 2026-11-02T01:05Z على main@fbe6472e. **لا شيء من أدناه نُشر** — المسودات انتظار قرار المستخدم (POLICY: نص معتمد فقط يُنشر).

## C-1 — P10: release بلا overflow-checks (الخطورة: متوسطة-منخفضة — robustness)
- **المشكلة:** `[profile.release]` في Cargo.toml يضبط `panic = "abort"` لكنه لا يفعّل `overflow-checks`؛ في release يلتفّ الطفحان الحسابي بصمت بينما يذعر في dev. في نواة تتوقف كليًا عند الذعر، الالتفاف الصمت أسوأ نمط فشل: حسابات الأطوال والفهارس الملفوفة قد تتجاوز منطق الحدود بلا أي إشارة. سياقنا: 3,293 موقع فهرسة غير ثابتة (heuristic، d11c126a) وبعضها يحسب أحجامًا مشتقة من مدخلات guest (gzip ISIZE #20، PAX #17).
- **الدليل:** `v2/artifacts/TA/cargo_profiles.txt`؛ تحقق main@fbe6472e: لا مفتاح overflow-checks [MEASURED].
- **نظام التحقق:** `git show fbe6472e:Cargo.toml | grep overflow` (فارغ)؛ ثم قياس كلفة التفعيل على زمن البناء/الإقلاع.
- **المسودة (EN، ≤120 كلمة، بانتظار الاعتماد):**
> The release profile in `Cargo.toml` sets `panic = "abort"` but does not enable `overflow-checks`, so release builds wrap on integer overflow silently while debug builds panic. In a kernel whose failure mode is a full halt, silent wraparound is arguably the worse outcome: index or length arithmetic that wraps can bypass bounds logic with no observable signal. A static audit at `d11c126a` counted 3,293 non-constant indexing sites (declared heuristic), several computing sizes derived from guest-controlled values (gzip ISIZE, PAX headers). Consider enabling `overflow-checks = true` for `[profile.release]`, measuring the boot-time and size cost, and adding one regression test on a wrapping size computation. Verified present at main@fbe6472e (no `overflow-checks` key).

## C-2 — P15: مخاطر نمطية للشيفرة المولّدة آليًا (الخطورة: معلوماتية)
- ملاحظة عملية (23% من الأسطر مولّدة، إشراف اتجاهي لا سطري) وليست عيب كود محدد؛ **بلا مسودة علنية** — رأي يخص منهجية المشروع، يناقش فقط إن طلبت أنت ذلك.
- الدليل: `docs/paper/STEERING-PROVENANCE.md`؛ Critical 7.3.4.

## C-3 — P14: COW معطّل لمسار forks (الخطورة: منخفضة — دَين أداء معلن)
- قرار تصميمي يعلنه المستودع نفسه؛ اقتراح علني لن يضيف معلومة جديدة ⇒ **بلا مسودة** (أُسقط من المساهمات: مطروح ذاتيًا في وثائقهم).

## C-4/C-5 — P16 (فرق عدّ unsafe fn 108/110) وP17 (غياب خط الأساس في v1)
- منهجيتان داخليتان لتقييمنا، لا تعيبان Ginux ⇒ بلا مسودة؛ تُحفظان للأرشفة في docs/HISTORY.md عند الحاجة.

---
**الأمنية:** لا توجد مشاكل C من فئة "أمنية خاصة" في هذه الجولة — P10 صيغت كـrobustness لا كادعاء أمني (POLICY Tier-2 يظل مفعّلًا لأي نشر).

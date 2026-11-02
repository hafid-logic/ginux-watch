# matrix.md — مصفوفة التقاطع: مشاكلنا (P1–P17) مقابل upstream

- **آخر فحص:** 2026-11-02T01:05Z على `main@fbe6472e5cc3302b09920119dada5770933a045b` (قراءة/grep/عدّ فقط — `git grep`/`git show`، دون تشغيل كود). فحص تكميلي 02:12Z على `origin/main@1203e291` (أسطح البناء لصف P10؛ رأس تقدّم 9 commits منها دمج PR #41)؛ تحقق نشر P10 بـGET في 02:59Z (issue #43 — مطابقة حرفية).
- **المصادر:** `download/REPORT-v2-static.md` + `download/v2/TA–TH.md` (أدلة: `download/v2/artifacts/T*/`) + `download/Ginux_Critical_Section_AR.md` + `download/Ginux_Executive_Summary_AR.md` + `download/Ginux_Rust_Assessment_AR.md` + F1–F8 من STATE.md. الشجرة المفحوصة أصلاً: `d11c126a` (2026-10-29) و`36503bda`/`759cf2e2` لاحقًا.
- **المنهجية:** T-B (خط أساس) وT-G (تصنيف أعمى لالتزامات upstream) مهام منهجية بلا صفوف P (errata داخلية). التصنيف بالمسارات والدوال والكلمات المفتاحية لا بالعناوين.
- **الأصناف:** A مطابق | B مشابه (نفس العائلة/الملف/الجذر) | C غير مطروح | D أُصلح (تحقق قراءةً في main).
- **الإحصاء:** A=1، B=7، C=5، D=4 (17 صفًا).
- **upstream-dump:** `work/upstream-dump/` (41 بندًا حتى #41، تعليقات وملفات وSHA دمج؛ snapshot 2026-11-02T00:50Z).

| P | العنوان | المصدر | الصنف | المقابل | الحالة على main | الدليل | الثقة |
|---|---|---|---|---|---|---|---|
| P1 | QEMU 10.0.13 يسحق virtio-net queue إلى 1024 وboot.sh يطالب 256 → فشل البوابات | STATE F1؛ reports/2026-11-02.md | **A** | #4 (أُصلح بـ#10+#13؛ أُغلق #4) | **زالت** | boot.sh@main يقبل regex 8…32768 [MEASURED]؛ CI 41364863523 PASS على 1024/256 | عالية |
| P2 | 3,293 فهرسة غير ثابتة + panic=abort → أي تجاوز = توقف كلي (سطح DoS) | TA A2؛ Critical 7.1.2/7.3.1 | **B** | #17، #20، #21 (أُصلح #38)، #22 + #5 (اختبار) | **قائمة** (بنيويًا؛ الحالات المحددة: #21 زالت) | Cargo.toml@main: panic=abort في المسارين بلا overflow-checks [MEASURED] | عالية |
| P3 | تغطية SAFETY 8.2%/9.9% وفجوات بنية (services/ وlinux_socket.rs ≈0%) | TH H1/H3؛ Critical 7.1.3 | **B** | #5 بند unsafe-inventory (جزئيًا في #9) | **قائمة جزئيًا** | kernel/src@main: 109 `SAFETY:` مقابل ~1,033 كتلة unsafe؛ linux_socket.rs = 1 [MEASURED]؛ clippy-kernel landed (Makefile:277) | عالية |
| P4 | 94 واجهة آمنة غير محصنة (33 ترجع `&'static mut`)؛ `global_manager_mut` بـ38 مستدعى | TF؛ STATE F3 | **B** | #5 بند 3 + #7 (ownership gates) | **قائمة** | `fn global_manager_mut` موجود domain.rs:3222@main [MEASURED] | عالية |
| P5 | `FrameLease` هو Copy → ملكية الإطارات غير مفروضة نوعيًا | TF؛ STATE F4 | **B** | عائلة #26/#27/#28/#29 (إصلاح فردي #37) | **قائمة** | `#[derive(Clone, Copy…)]` فوق struct FrameLease@main [MEASURED] | متوسطة (الجذر نوعي مقصود للسجلات المعبأة)؛ الحضور عالية |
| P6 | ~100 `static mut` + افتراض vCPU واحد → سباقات عند SMP | Critical 7.1.4؛ STATE F8 | **B** | #5 بندا 3–4 + #7/#8 (spinlocks، KERNEL_ENTRY_LOCK) + #25 (مثال SMP) | **تُعالج جزئيًا** | static mut في kernel/src: 100@d11c126a → **36**@main [MEASURED]؛ سكربتات writable-globals موجودة | عالية |
| P7 | نسخ uname إلى المستخدم (08f9df46): افتراض حجم داخلي غير مفحوص | TD؛ errata E6/E7 | **D** | إصلاح upstream ذاته 08f9df46 ثم #7 | **زالت** | `ginux_raw_copy_{from,to}_user` بـfixups موجودة cpu.rs:2178+@main [MEASURED] | عالية |
| P8 | لا تثبيت/تسجيل إصدارات QEMU/OVMF في doctor؛ فشل معتمد على البيئة | TE E1/E2؛ Critical 7.2 | **B** | عائلة #14 + #31 (aw-bits) — CI أُضيف في #9 | **قائمة جزئيًا** | doctor.sh@main يفحص `check_command qemu-system-x86_64` فقط، لا إصدارات [MEASURED]؛ CI موجود (.github/workflows/check.yml) | عالية |
| P9 | provenance الورقة: استشهاد 9afa6176 وأرقام تطابق d11c126a | STATE F7 | **D** | لا نظير مباشر (#5 يتناول 3.31× بندًا مختلفًا) | **زالت في المستودع** | الورقة@main تعلن `\evaluatedcommit{d11c126a…}` [MEASURED]؛ نسخة Zenodo نفسها [UNVERIFIED] | عالية |
| P10 | release بلا `overflow-checks` → التفاف حسابي صامت | TA A3 | **C** | لا نظير (dump scan 02:12Z: صفر نقاش overflow-checks) | **منشور — issue #43** (نشر المستخدم اليدوي 2026-11-02 بإذن صريح؛ GET: مطابقة حرفية؛ job 494920 أُلغي) | Cargo.toml@fbe6472e و1203e291 بلا overflow-checks؛ لا .cargo/؛ لا RUSTFLAGS/CARGO_PROFILE_*/debug-assertions؛ `PROFILE ?= release` (Makefile:4) وCI make بلا تجاوز [MEASURED] | عالية |
| P11 | ملفات عملاقة: cpu.rs 44,324 سطرًا | Critical 7.1.5 | **B** | #5 بند 5 (تحليل #7/#9 جارٍ) | **تُعالج جزئيًا** | cpu.rs: 44,324@d11c126a → **42,752**@main [MEASURED] | عالية |
| P12 | تناقض وثائقي: بوابات "خضراء" تاريخية مقابل فشل معلَن عند المثبَّت | TE E2؛ Critical 7.3.2 | **D** | #9 (CI) + بوابات HDAE الموثقة | **زالت عمليًا** | check.yml@main؛ make test PASS على main (run 41364863523) [MEASURED] | عالية |
| P13 | سجل التوافق: 82 "Complete" تشمل ENOSYS stubs | Critical 7.3.5 | **D** | #5 compat + #9 (و#11 أُلغيت لصالحها) | **زالت** | 19 entry "Unsupported" في LINUX-COMPATIBILITY.md@main [MEASURED] | عالية |
| P14 | COW معطّل لمسار forks (دَين أداء معلَن) | Critical 7.3.3 | **C** | لا نظير — قرار تصميمي معلن | **قائمة (بالتصميم)** | وثائق المشروع نفسها تعلنه | عالية |
| P15 | مخاطر نمطية للشيفرة المولّدة آليًا (23% مولّدة؛ إشراف اتجاهي) | Critical 7.3.4 | **C** | لا نظير — ملاحظة عملية لا عيب كود | غير محسوم (فلسفي) | STEERING-PROVENANCE.md@main | متوسطة |
| P16 | فرق عدّ unsafe fn 108/110 غير محسوم | TH H2 | **C** | لا نظير — منهجي داخلي | n/a | TH_summary.json | عالية (أنه غير محسوم) |
| P17 | غياب خط أساس أدى لتفسير 26.7% الخاطئ | TB B4؛ errata E5 | **C** | لا نظير — منهجي داخلي | n/a | TB_summary.json | عالية |

## حكم الحالة على main (تلخيص البند 4 من التوجيه)
- **زالت:** P1 (بإصلاح #10+#13)، P7 (hardening 08f9df46+#7)، P9 (الورقة تستشهد d11c126a الآن)، P12 (CI landed)، P13 (Unsupported ledger landed).
- **تُعالج جزئيًا:** P6 (static mut 100→36)، P11 (cpu.rs −1,572 سطرًا)، P3 (clippy+baseline landed؛ الفجوة باقية)، P8 (CI landed؛ إصدارات doctor باقية).
- **قائمة:** P2 (بنيويًا)، P4 (global_manager_mut)، P5 (FrameLease Copy)، P10 (overflow-checks — **منشورة: issue #43**، نشر المستخدم اليدوي 2026-11-02 بإذن)، P14 (بالتصميم).
- **غير محسوم:** P15، P16، P17 (منهجية/عملية).

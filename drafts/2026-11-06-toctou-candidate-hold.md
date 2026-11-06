# مرشح C1 (TOCTOU ptrace/SYSEMU) — HOLD بشرط التوقف الفوري (v5.0، 2026-11-06)

- **المرشح (كما وُجِّه):** جدول لكل syscall في مسارات ptrace/SYSEMU في `ginux-init` (passthrough أم emulate؟ مع file:line) + هل تُنسخ الوسائط المؤشرية من ذاكرة الـtracee قبل الفحص؛ الفرضية «المحاكاة غير متأثرة» [INFERRED حتى تثبت] — وإن وُجد مسار passthrough بوسائط مؤشرية: تصميم اختبار متعدد الخيوط (نص فقط) + معيار الفشل.
- **زناد التوقف الفوري (MEASURED 2026-11-06T02:0xZ): تداخل مباشر مع PRs مفتوحة** — ملفات PRs المفتوحة (جُلبت حيًا):
  - **#207** (مفتوح): `crates/ginux-init/src/main.rs` + `dispatch.rs` + `channel_hooks.rs` + `launch.rs` + `tests/fixtures/launch-fixture.c` + `scripts/test-launch.py` + `crates/ginux-core/src/lib.rs` + `README.md`.
  - **#221** (مفتوح؛ created_at 2026-11-06T00:23:31Z — المصدر inbox/upstream-dump/issues-updated-2026-11-06.json، dump جلسة 32): `crates/ginux-init/src/main.rs` + `supervisor.rs` + `Makefile` + `tests/fixtures/process-review-fixture.c` + `scripts/test-process-native.py`.
  - مساحة المرشح (`main.rs`/`supervisor.rs`/`dispatch.rs`) ⊂ ملفات كلي الـPRs ⇒ جدول file:line سيصبح قديمًا بدمجهما، وأي «PR مختبَر» من هذا التحليل يخالف قيد POLICY 2b (لا تداخل) أثناء فتحهما.
- **ما لم يُنفَّذ بسبب التوقف:** جدول الـsyscalls، فحص نسخ الوسائط المؤشرية، تصميم الاختبار متعدد الخيوط، الانتقال لمرشح ثانٍ (بند C8) — لم يقرأ المُشغِّل أي جزء من الكود لهذا الغرض.
- **الخيارات المعروضة للمستخدم:**
  - (أ) الانتظار حتى حسم #207/#221 (دمج/إغلاق) ثم إعادة تفعيل المرشح على الشجرة الجديدة بإعادة قياس المواقع.
  - (ب) تجاوز صريح يسمّي أنه تحليل قرائي فقط على `64a3e3f7` بلا أي PR — يُسجَّل خطوه في هذا الملف ويُعاد التحقق قبل أي استخدام.
  - (ج) مرشح بديل خارج ملفات الـPRs المفتوحة (يُقترح ويعرض قبل أي تنفيذ).
- **بند 9 محفوظ:** fuzz (بوابة 13) يبقى تصميمًا فقط حتى 2026-11-12 — لا تشغيل قبل تسجيل المدة والأهداف والسقف.

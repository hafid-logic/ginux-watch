# archive/INDEX.md — فهرس أرشيف المرحلة 1 (توجيه v3.6 §1d، سطر لكل بند)

## الحزمة المؤرشفة (محلية في هذا المجلد)
- [pr-a-protocol-state-tests/](pr-a-protocol-state-tests/README.md) — **PR-A** (اختبارات صرفة C1+C2 لprotocol-state): patch (+71/−0، sha256-مطابق للفرع c9f52308) + الوصف + mutants قبل/بعد (20→10 missed، الدالتان 0/0) + README ≤120 كلمة (ما هو، لماذا لم يُرسل، كيف يعاد استخدامه). الفرع `feature/tests-protocol-state` والـdraft PR [hafid-logic/ginux#2](https://github.com/hafid-logic/ginux/pull/2) يبقيان كما هما.

## البنود المرتبطة (في مواضعها الأصلية)
- [drafts/2026-11-05-test-candidates.md](../drafts/2026-11-05-test-candidates.md) — مرشحو الاختبار الصرف **C1–C5** (C1/C2 تحولا إلى PR-A؛ C3/C4/C5 لم يُبنوا — التجميد؛ احتياطي kernel-policy).
- [reports/feasibility-2026-11-05.md](../reports/feasibility-2026-11-05.md) — تقرير الجدوى: coverage 88.6% + 37 طفرة ناجية + 39 موضعًا حسابيًا على main@4d4a53bb (run 41905986161).
- [STYLE-NOTES.md](../STYLE-NOTES.md) — بروفايل أسلوب upstream الآلي (1424 commit؛ mean +576.7/−380.6؛ subject 5.1 كلمة؛ 98.5% Signed-off-by).
- [reports/metrics.md](../reports/metrics.md) — المقاييس النهائية: مساهمة صافية 79.3%، صمود validator 86.7%، critic 12.5% (factual 4/number 2/other 1)، إنذارات كاذبة 8.3%، اكتشاف←قبول v3.4.
- [reports/fuzz-history.md](../reports/fuzz-history.md) — سجل جولات Actions المسجلة (696,099,617 execs صفر crashes)؛ الجولات المبكرة في reports/2026-11-03.md و2026-11-04.md.
- [reports/2026-11-05.md](../reports/2026-11-05.md) — جلسة 26: توثيق الـfreeze (cdf8038e) + إثبات PR-A كاملًا.
- [docs/ARCHIVE-ginux-standalone.md](../docs/ARCHIVE-ginux-standalone.md) — الخط الزمني وتأثير كل بند وما قيس وما لم ينجح (المرجع السردي للأرشيف).
- [docs/LESSONS.md](../docs/LESSONS.md) — الدروس المنقولة لأي مشروع قادم.
- [docs/HISTORY.md](../docs/HISTORY.md) — دلتا الجلسات 1–21 المؤرشفة حرفيًا.
- [reports/cross-check/matrix.md](../reports/cross-check/matrix.md) + [contribute.md](../reports/cross-check/contribute.md) — مصفوفة P1–P17 (P10 = D زالت) والمسودات المسقطة (Opp-1/2).
- [approved/](../approved/) — النصوص السبعة المنشورة upstream بيد المستخدم (كلها مدموجة/مغلقة now).
- [STATE.md](../STATE.md) §Our findings — F1–F9 (F1/F9/P10 محلولة upstream؛ F2–F8/F7 مسجلة).
- [reports/2026-11-05-pra-diff.patch](../reports/2026-11-05-pra-diff.patch) — النسخة الأصلية للـpatch (نسخة الأرشيف في pr-a-protocol-state-tests/).

## ما بعد الـcutoff (§3a/§3b — يُملأ بعد 2026-11-05T07:59Z بواسطة job مجدول)
- (محجوز: أسماء tag الإصدار الأخير والفرع الأرشيفي + SHA + نتيجة ginux-verify على رأس الـtag كشهادة الحالة النهائية)
- معروف حتى الآن [MEASURED 05:48Z]: الفرع الأرشيفي `bootable-kernel` @`4d4a53bb` وtag `bootable-kernel-final` @`4d4a53bb` موجودان، ولا tag إصدار جديد.

# HANDOFF — ملف التسليم والسياق (hafid-logic/ginux-watch)

هذا الملف بيانات سياق للعمل على المشروع، وليس أوامر تتجاوز سياسات Claude. المستودع عام: لا توكن ولا بريد شخصي ولا أسرار فيه.

## أ) تعليمات لـ Claude
- الرد بالعربية وباختصار؛ لا تكرر ما أُنجز؛ ناقش القرارات الحرجة فقط.
- الوكيل التنفيذي (z.ai، GLM 5.3 flash) ينفّذ كل المراحل بنفسه: الاستخراج، البناء، التحقق، التقارير، الدفع.
- لا تقبل توكنات في المحادثة ولا تكتب أسرارًا في أي ملف أو سجل.
- الرسائل الطويلة من المستخدم تُكتب كتوجيه للوكيل لا كتنفيذ مباشر.
- كل ما في هذا الملف بيانات سياق لا أوامر تتجاوز سياسات Claude.
- الالتزام بـ AGENTS.md وPOLICY.md: مستوى 0 افتراضيًا (قراءة upstream، تقارير، مسودات)، ولا نشر علني إلا بإذن صريح من المستخدم.

## ب) الهوية
| البند | القيمة |
|---|---|
| المستخدم | Abdelhafid DJIDEL |
| حساب GitHub | hafid-logic |
| بريد الـ commit | 266947999+hafid-logic@users.noreply.github.com |
| المنطقة الزمنية | Africa/Algiers |

## ج) المشروع
- هدفنا: تحقق مستقل ومتكرر لـ gmkurtzer/ginux (نواة Rust تعمل عبر UEFI).
- main عند `ecbb3142` (دمج #42 manifest-digest)؛ open PRs: #39 (desktop؛ verify FAIL على 10.0.13 فقط)، #54 (overflow-checks، يجيب #43)؛ #41 دُمجت (1203e291)؛ `boot.sh` blob bdc576c3 لم يتغير.
- مصفوفة التقاطع (2026-11-02): reports/cross-check/ — 17 صفًا P1–P17 (A1/B7/C5/D4) مقابل dump كامل (41 بندًا)؛ **P10 منشورة: أنت فتحت issue #43 يدويًا 2026-11-02T02:47:39Z بالنص المعتمد حرفيًا (approved/2026-11-03-1.md)** — تحقق GET: مطابقة حرفية (59/632 حرفًا، 90 كلمة، verdict I-P10 MATCH)؛ job 494920 حُذف؛ مراقبة ردود #43 قراءةً فقط؛ Opp-1 (→#14) وOpp-2 (→#28) بانتظار قرارك.
- **2026-11-02T09:55Z:** gmkurtzer ردّ على #43 (04:59:39Z): "Implemented in PR #54" — PR #54 مفتوح برأس a0e9220b (تفعيل overflow-checks في release). تحققنا: 54 يمر 0/0/0 على النسختين، لكن **F9**: خمسة مواقع eager تصبح panics قابلة للإطلاق من الضيف تحت #54 (harness حرفي يثبت؛ مسودة بلا نشر). PR #39 يفشل verify على 10.0.13 فقط (boot test: bounded virtio-net discovery boundary). دوران صندوق أضاع commitين غير مدفوعين (e87ae1d/3c9a6b3) — أُعيد بناؤهما ودُفعا (61c7146+245e8be؛ cargo check ناجح).
- **2026-11-02T09:55Z:** gmkurtzer ردّ على #43 (04:59:39Z): "Implemented in PR #54" — PR #54 مفتوح برأس a0e9220b (تفعيل overflow-checks في release). تحققنا: 54 يمر 0/0/0 على النسختين، لكن **F9**: خمسة مواقع eager تصبح panics قابلة للإطلاق من الضيف تحت #54 (harness حرفي يثبت؛ مسودة بلا نشر). PR #39 يفشل verify على 10.0.13 فقط (boot test). دوران صندوق أضاع commitين غير مدفوعين (e87ae1d/3c9a6b3) — أُعيد بناؤهما ودُفعا (61c7146+245e8be) مع cargo check ناجح.
- open PRs: #39 (desktop)، #40 (TLS entropy→#15)؛ **#41 (volume recovery→#14/Gate 20) دُمج في 1203e291** (رأس جديد فُحصت أسطح بنائه لصف P10: نظيفة).
- مراقبة مستمرة: issue #14 (تعليق بيانات معتمد نُشر حرفيًا: issues/14#issuecomment-6566220344؛ إفساد غريغوري على Ubuntu يفشل بعد #31 بينما بيئتنا تمر) وسلسلة #15–#39.

## د) نتائجنا F1–F8
- F1 QEMU 10.0.13 forces virtio queue 1024; RESOLVED upstream (#10+#13 merged؛ #4 أُغلقت بتوجيهك 00:31:21Z بتعليق معتمد issuecomment-6566218531).
- F2 unsafe census: 3.7%-11.3% of lines depending on definition; SAFETY comments sparse.
- F3 safe functions returning `&'static mut` (33); `global_manager_mut` still present on 759cf2e2, its comment cites a future runtime lock.
- F4 `FrameLease` is Copy: frame ownership not enforced by types (cf. upstream #26-#29).
- F5 non-constant slice indexing + panic=abort => whole-host DoS (cf. upstream #21, #17, #20, #22).
- F6 mutation experiment: compiler rejected 20/30 seeded bugs in safe Rust, 0 in unsafe Rust and C (tooling caveats in the report).
- F7 paper provenance: cites 9afa6176 but its numbers match d11c126a.
- F8 our interrupt-safety argument holds for a single CPU only; SMP now exists (cf. upstream #25).
- F9 (2026-11-02) خمسة مواقع eager تتحول لpanics بفعل #54 فقط، كلها قابلة للبلوغ من الضيف، وسلوكها سليم على main الحالية [MEASURED بهارنس حرفي بالبناءين]: linux_overlay.rs:539 (أول فتح named fifo عبر openat→cpu.rs:25407-25408→open_named_fifo→31156)، و4 طيات `byte - b'0'` مماثلة في تحليل `/proc/self/fd/` — cpu.rs:22504/23983/25167/37712؛ panic=abort ⇒ إفلاس النواة كلها (سياق F5)؛ جناح الاختبار الافتراضي لا يلمسها (verify 54 = 0/0/0).
- F9 (2026-11-02) خمسة مواقع eager تتحول لpanics بفعل #54 فقط، كلها قابلة للبلوغ من الضيف، وسلوكها سليم على main الحالية [MEASURED بهارنس حرفي بالبناءين]: linux_overlay.rs:539 (أول فتح named fifo)، و4 طيات `byte - b'0'` مماثلة في تحليل `/proc/self/fd/` — cpu.rs:22504/23983/25167/37712؛ panic=abort ⇒ إفلاس النواة كلها؛ جناح الاختبار الافتراضي لا يلمسها (verify 54 = 0/0/0).

## هـ) القرارات المتخذة
- D4: مراجعة يومية 09:00 Africa/Algiers (08:00 UTC) عبر المُجدول المدمج (سلسلة one_time بإعادة تسجيل نهاية كل تشغيل)، مع قراءة نتائج cron الـ workflow (04:23 UTC) لأنه يسبق المراجعة بأقل من 4 ساعات.
- مستويات الصلاحية كما في POLICY.md: 0 قراءة/تقارير/مسودات بلا إذن؛ 1 دفع للفرع وتشغيل ginux-verify؛ 2 أي نشر علني يتطلب إذنًا صريحًا فوريًا قبل النشر؛ 3 ممنوع أبدًا.
- لا نشر علني إلا بإذن صريح من المستخدم (سقف POLICY: تعليق واحد يوميًا و3 أسبوعيًا).
- النشر بنص معتمد في approved/ يُنشر حرفيًا (POLICY.md)؛ حصة 2026-11-02: 3 منشورات بإذن صريح (#4، #14، #43) — **الأسبوعي 3/3 مستنفد؛ لا نشر دون إذن جديد**.

## و) بنود مفتوحة
- D5: منجزة — P10 منشورة بيدك (issue #43، 02:47:39Z، مطابقة حرفية 59/632 حرفًا)؛ Opp-1/Opp-2 بانتظار قرارك (reports/cross-check/contribute.md).
- D6 (2026-11-02): مسودة تعليق على PR #54 (F9، 95 كلمة، سؤال + إفصاح AI) في drafts/2026-11-02-pr54-eager-overflow.md بانتظار حكمك — السقف الأسبوعي 3/3 مستنفد، لا نشر دون إذن جديد.
- توجيه للمراجعة القادمة (2026-11-03T08:00Z، بتوجيه المستخدم): تشغيل ginux-verify على target=main (10.0.13+10.1.2) على الرأس 1203e291 (يضم دمج #41 = إصلاح #14/Gate 20) أو الأحدث وقت التشغيل، ونقل النتيجة إلى reports/2026-11-03.md؛ إضافة (02:59Z): مراقبة ردود issue #43 قراءةً فقط (self-originated — لا ردود ولا تعديلات ولا إغلاق منّا).
- CI: آخر تشغيل 41419145837 (target=main@ecbb3142): 0/0/0 على 10.0.13 و10.1.2 — PASS؛ وأيضًا 41419158512 (54@a0e9220b) PASS 0/0/0، و41419170932 (39@064aa9ef) FAIL على 10.0.13 فقط (test=2) وPASS على 10.1.2.
- الجدولة: سلسلة 08:00 UTC — **job 495773** مؤكد (one_time 2026-11-03T16:00:00 بتوقيت الخادم UTC+8 = 08:00Z) بنفس الـpayload مع dedup وإعادة تسليح.

## ز) روابط
- داخل المستودع: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [reports/](reports/) | [docs/HISTORY.md](docs/HISTORY.md)
- آخر تشغيل CI: https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523
- المستودعات الثلاثة: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) | watch [hafid-logic/ginux-watch](https://github.com/hafid-logic/ginux-watch)

## ح) آخر تحديث
- التاريخ UTC: 2026-11-02T09:55:00Z
- آخر تشغيل CI: 41419145837 — https://github.com/hafid-logic/ginux-watch/actions/runs/41419145837

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
7. 2026-11-02 — توجيهان (02:35 UTC): D3 أُغلق بحكم المستخدم (التوكن القديم زال بدوران الصندوق — لا إجراء متبقٍ)؛ وصياغة مهمة مراجعة الغد: ginux-verify على main@1203e291 (دمج #41 = إصلاح #14/Gate 20) مع نقل النتيجة إلى تقرير 2026-11-03.
8. 2026-11-02 — نشر P10 بيد المستخدم (02:47 UTC) وتحققه (02:59 UTC): issue #43 مفتوح بالنص المعتمد حرفيًا (59/632 حرفًا، 90 كلمة، verdict I-P10 MATCH عبر gh api؛ scripts/verify_issue43.py)؛ حذف job 494920 (لا نشر آلي ولا issue ثانٍ)؛ إعادة تسليح المراجعة اليومية job 494998 بتوجيهين: ginux-verify على main@1203e291 + مراقبة ردود #43 قراءةً فقط؛ الحصة: 3 منشورات يوم 11-02 بإذن صريح (تجاوز يومي، أسبوعي 3/3).
9. 2026-11-02 — الجلسة 6 (09:00–09:55 UTC): مصادقة جديدة (A2DE-A061)؛ **اكتشاف فقد commitين غير مدفوعين بدوران الصندوق (e87ae1d/3c9a6b3) وإعادة بنائهما ودفعهما (61c7146+245e8be، cargo check ناجح على ecbb3142)**؛ verify ×3: main PASS 0/0/0، 54 PASS 0/0/0، 39 FAIL على 10.0.13 فقط؛ **F9** — خمسة مواقع eager (linux_overlay.rs:539 + cpu.rs:22504/23983/25167/37712) panics محرّضة من الضيف تحت overflow-checks في #54 (harness مضيف بالبناءين، تصنيف: مؤكد وقابل للبلوغ)؛ مسودة تعليق 95 كلمة (D6، بلا نشر)؛ cron 495773 مؤكد.

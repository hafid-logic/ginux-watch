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
- main عند **`82df3d71`** (دمج #46 domain-memory؛ observed 01:14Z مع verify 41558410745 — بلا مس للفجوة/FrameLease)؛ `boot.sh` لم يتغير عن النسخة المتحققة (blob bdc576c3؛ تغييرات #41 على boot.sh أضافت artifact-dir فقط)؛ PR #39 يبقى FAIL على 10.0.13 فقط (run 41419170932).
- السرد التاريخي (مصفوفة التقاطع، ردود #43/#54، v2.2..v2.6 بالتفصيل): docs/HISTORY.md (مؤرشفة حرفيًا في v2.7)؛ الحالة الجارية في STATE.md.

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

## هـ) القرارات المتخذة
- D4: مراجعة يومية 08:00 UTC (09:00 Africa/Algiers) — سلسلة one_time بإعادة تسجيل نهاية كل تشغيل؛ قراءة نتائج cron الـ workflow لأنه يسبق المراجعة.
- النشر: مستويات POLICY.md (0/1/2/3)؛ نص معتمد في approved/ يُنشر حرفيًا؛ السقف 1 يوميًا و3 أسبوعيًا؛ حصة 2026-11-02 = 4 منشورات (الأخير بتجاوز أسبوعي مأذون لمرة واحدة)؛ أي نشر جديد يتطلب إذنًا جديدًا.

## و) بنود مفتوحة
- D5..D12 كلها منجزة/محسومة — النصوص الحرفية: docs/HISTORY.md؛ الخلاصة الجارية: STATE.md (Pending decisions).

- توجيه للمراجعة القادمة (2026-11-03T08:00Z — مُحدّث بتوجيه v2.5-2): **ginux-verify على رأس PR #54 (47fc22c8 وقت الكتابة — يُحل الرأس وقت التشغيل)** و**target=main فقط إن دُمج #54** (dedup: main تحقق مرتين على 82df3d71 = 41554808432 + 41558410745)؛ **قراءة حالة conflicts فقط** لـ#54 (mergeable_state = dirty، قراءة فقط بلا إجراء)؛ تسجيل نتيجة fuzz 41562800441 (30 دقيقة tar/PAX @82df3d71) إن لم تُسجل؛ **لا تعليقات علنية جديدة حتى نتيجة جديدة بدليل (v2.5-4 — المسودتان مؤجلتان و#38 مُسقط)**؛ مراقبة #43 قراءةً فقط (self-originated — لا ردود ولا تعديلات ولا إغلاق منّا).
- CI: آخر تشغيل 41419145837 (target=main@ecbb3142): 0/0/0 على 10.0.13 و10.1.2 — PASS؛ وأيضًا 41419158512 (54@a0e9220b) PASS 0/0/0، و41419170932 (39@064aa9ef) FAIL على 10.0.13 فقط (test=2) وPASS على 10.1.2.
- الجدولة: سلسلة 08:00 UTC — **job 498132** (أُعيد إنشاؤه 2026-11-03 بـpayload v2.5 بعد حذف 495773؛ one_time 2026-11-03T16:00:00 بتوقيت الخادم UTC+8 = 08:00Z) مع dedup وإعادة تسليح.

## ز) روابط
- داخل المستودع: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [reports/](reports/) | [docs/HISTORY.md](docs/HISTORY.md)
- آخر تشغيل CI: https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523
- المستودعات الثلاثة: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) | watch [hafid-logic/ginux-watch](https://github.com/hafid-logic/ginux-watch)

## ح) آخر تحديث
- التاريخ UTC: 2026-11-03T06:1xZ (v2.7: fuzz تفاضلي PAX 15.27M + المثيل الثالث volume_surfaces 87.85M — صفر crashes — مسودة issue معروضة للمستخدم فقط؛ جلسة 15)
- آخر تشغيل CI: محلي بالكامل (cargo fuzz 0.13.2/nightly على upstream@82df3d71 path-dep)؛ قبله fuzz CI 41562800441 (106.1M execs) وginux-verify 41558410745 (0/0/0 على النسختين)

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
14. 2026-11-03 — v2.5: المسودتان مؤجلتان و#38 مُسقط؛ fuzz.yml pin 82df3d71؛ أول fuzz 30 دقيقة = 106,140,505 execs صفر crashes؛ job 498132 للمراجعة؛ قاعدة POLICY «لا تعليقات بلا نتيجة جديدة». (النص الكامل: docs/HISTORY.md)
13. 2026-11-03 — v2.4: verify مُعاد على main@82df3d71 = 0/0/0 (41558410745)؛ D8 مؤجلة + قاعدة «لا إعلان عمل غير مبني»؛ D9 تصميم فقط؛ D12 #38 غير قابلة للاختبار مضيفًا. (النص الكامل: docs/HISTORY.md)
12. 2026-11-03 — v2.3: فجوة #26 سالبة (مسودة معتمدة-بشرط-1)؛ بطاقة builder غير قابلة للتنفيذ (D10)؛ #41 معطوبة مؤكدة (D11)؛ #54: الصيانة أكدت F9، رأس 47fc22c8؛ مصادقة جديدة؛ dump 57 بندًا؛ verify 41554808432 = 0/0/0. (النص الكامل: docs/HISTORY.md)
11. 2026-11-02 — team v2.1: بنية كاملة + تجربة قياسية (توازٍ 492s مقابل 1148s = تحسن 57.1% → اعتماد)؛ درس: pull --rebase قبل commit. (النص الكامل: docs/HISTORY.md)
10. 2026-11-02 — نشر تعليق PR #54 حرفيًا منك (D6؛ GET مطابقة بايت 659/659، I-P54 MATCH)؛ سُجل في STATE/HANDOFF/matrix. (النص الكامل: docs/HISTORY.md)
9. 2026-11-02 — الجلسة 6: مصادقة جديدة؛ فقد commitين غير مدفوعين بدوران الصندوق وإعادة بنائهما؛ verify ×3 (main/54 PASS، 39 FAIL على 10.0.13)؛ اكتشاف F9 بخمسة مواقع eager؛ مسودة تعليق 95 كلمة؛ cron 495773. (النص الكامل: docs/HISTORY.md)
8. 2026-11-02 — نشر P10 بيد المستخدم + تحققه (issue #43 مطابقة حرفية I-P10 MATCH)؛ حذف job 494920؛ إعادة تسليح المراجعة اليومية؛ الحصة 3 منشورات بإذن صريح. (النص الكامل: docs/HISTORY.md)



15. 2026-11-03 — v2.6 (قياس قبل التشغيل): جرد + أعلام + corpus سليمة [MEASURED]؛ harness موسّع لنداء النواة كاملًا + بذور 53 + oci.dict؛ جولة oci_surfaces 41M execs صفر crashes (تغطية A 66.27 → C 93.18 regions/97.94% دوال)؛ المحلل الثاني protocol-state 247M execs صفر crashes (97.50%/100%)؛ لا نشر — نتائج سالبة؛ درس: القواميس والبذور فقط تُلتزم. (النص الكامل: docs/HISTORY.md)

16. 2026-11-03 (05:0x–06:1x UTC) — توجيه v2.7: **(2) fuzz تفاضلي ginux-oci ↔ crate tar**: oracle مشترك (رؤية النواة 256B مقابل tar 0.4 على نفس البايتات) + مصفوفة 33 حالة + هدف libFuzzer تسجيلي بـdedup هاشي؛ 3×300s = **15,272,896 execs صفر crashes** (لا ginux ولا tar)؛ 15,339 اختلافًا فريدًا → **5 أسباب جذرية** (عيّنة probe لكل فئة): tar يُظهر pseudo-entries (XHeader عند pax تالف/XGlobalHeader دائمًا) = انزياح فهرسة؛ ginux fail-closed صارم (4,098)؛ tar أكثر صرامة (multi-x + غير-UTF8؛ 2,098)؛ **انحراف PAX-size = الاكتشاف التوافقي الوحيد** (11/11b)؛ قيم PAX بـ\n مضمن (ginux ملتزم المواصفة)؛ repro صغير 1,638B (حالة 32)؛ إصلاح harness واحد (truncate char-boundary — لا يُحسب)؛ **لا finding أمنيًا**؛ **(3) المثيل الثالث volume_surfaces** (مرتبة 2، نقية): سلسلة النواة Record::decode→HostVolumeHeader::decode + probe مباشر + encode؛ بذور 26 بself-test + volume.dict + خطوة CI ثالثة؛ **تغطية A 98.85/100/100 → C 99.43/100/100** (بارييه دفاعي وحيد u16::try_from)؛ 3×560s = **87,846,486 execs صفر crashes** (~52.2k/s الأسرع)؛ **(1) مسودة issue** «Offering fuzz targets for PAX/OCI and ARP/IPv4/ICMP parsers» (115 كلمة، أرقام+pin 82df3d71+رابط المستودع+سؤالا fuzz//tests//CI+إفصاح AI) **لُصقت للمستخدم فقط بلا نشر**؛ البوابة التكرارية: dump محدث (57 بندًا، main GET = 82df3d71) **سالبة** (#44/#17 سياق فقط)؛ **(4) لا نشر**؛ الدفعات: 96189be → a42c184 → نهائي.

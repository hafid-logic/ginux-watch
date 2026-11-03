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
- **issue #58 (مسودة fuzz، توجيه v2.7-1):** نُشرت **بيدك يدويًا** 2026-11-03T06:23:25Z — https://github.com/gmkurtzer/ginux/issues/58 (hafid-logic، open)؛ تحقق GET: **I-F58 MATCH 12/12 بنود حاسمة** (893 حرفًا/128 كلمة — الإرشاد ≤120 موثق؛ **المنشور لا يطابق حرفيًا** المسودة المحفوظة drafts/2026-11-03-v27-fuzz-offer.md (115w): عدّلتَ قبل النشر — وسّعت العنوان +volume-format، حذفت نسب functions وسؤال CI الأسبوعي، أضفت نتيجة fail-closed؛ snapshot + الفروقات الثمانية في approved/2026-11-03-2.md + scripts/verify_issue58.py)؛ الأرقام: 41.0M/247.1M/87.8M execs + 15.3M differential، regions 93.2/97.5/99.4%، ASan+overflow-checks، pin 82df3d71، «not a safety claim» حاضرة. **ردّ الصيانة [OBSERVED، قراءة فقط]:** gmkurtzer 06:32:50Z (issuecomment-6597103730): يرحّب، ويطلب **fuzz/ علويًا لا tests/**، ويرحّب بـdraft PR ضد main بشروط 5 (أهداف+dictionaries/seeds؛ fuzz/README بأوامر دقيقة؛ smoke محدود؛ لا crash artifacts/corpus منتفخ؛ pinned commit+run summary في وصف PR) — PR واحد مقبول. **لا رد قبل اعتمادك**؛ أرقام المنشور موثقة داخليًا (reports/2026-11-03.md §13 + دلتا 16) — ملف fuzz-quality.md المستقل غير منشأ.
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
- التاريخ UTC: 2026-11-03T07:1xZ (تحقق issue #58 المنشورة يدويًا: I-F58 MATCH 12/12 بنود + عدم مطابقة حرفية للمسودة المحفوظة موثقة + تسجيل ردّ الصيانة — قراءة فقط؛ جلسة 17)
- آخر تشغيل CI: محلي بالكامل (cargo fuzz 0.13.2/nightly على upstream@82df3d71 path-dep)؛ قبله fuzz CI 41562800441 (106.1M execs) وginux-verify 41558410745 (0/0/0 على النسختين)

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
8.–14. (2026-11-02..03 — مؤرشفة حرفيًا في docs/HISTORY.md، deltas 8-11 و12-14): نشر P10 بيدك (issue #43 مطابقة حرفية) + تعليق PR #54 حرفيًا (D5/D6)؛ team v2.1 وتوازي 57.1%؛ v2.3 (فجوة #26 سالبة، D10/D11، مصادقة، dump 57)؛ v2.4 (verify 41558410745 = 0/0/0؛ D8 مؤجلة + قاعدة «لا إعلان عمل غير مبني»؛ D9 تصميم؛ D12 #38 غير مضيفيًا)؛ v2.5 (fuzz 106,140,505 execs صفر crashes؛ fuzz.yml pin 82df3d71؛ قاعدة «لا تعليقات بلا نتيجة جديدة»).

15. 2026-11-03 — v2.6 (قياس قبل التشغيل): جرد + أعلام + corpus سليمة [MEASURED]؛ harness موسّع لنداء النواة كاملًا + بذور 53 + oci.dict؛ جولة oci_surfaces 41M execs صفر crashes (تغطية A 66.27 → C 93.18 regions/97.94% دوال)؛ المحلل الثاني protocol-state 247M execs صفر crashes (97.50%/100%)؛ لا نشر — نتائج سالبة؛ درس: القواميس والبذور فقط تُلتزم. (النص الكامل: docs/HISTORY.md)

16. 2026-11-03 (05:0x–06:1x UTC) — توجيه v2.7: **(2) fuzz تفاضلي PAX↔tar**: 3×300s = 15,272,896 execs صفر crashes؛ 15,339 اختلافًا فريدًا → 5 أسباب جذرية (انحراف PAX-size = الاكتشاف التوافقي الوحيد؛ لا finding أمنيًا)؛ repro 1,638B (حالة 32)؛ **(3) volume_surfaces** (المثيل الثالث): 3×560s = 87,846,486 execs صفر crashes، تغطية C 99.43/100/100؛ بذور 26 + volume.dict + خطوة CI ثالثة؛ **(1) مسودة issue 115 كلمة لُصقت للمستخدم فقط بلا نشر**؛ dump محدث **سالبة** (البوابة التكرارية)؛ **(4) لا نشر**. (النص الكامل: docs/HISTORY.md، delta 16)

17. 2026-11-03 (~07:1x UTC) — **نشرتَ مسودة fuzz يدويًا: issue #58** (06:23:25Z، hafid-logic، open)؛ تحقق GET: **I-F58 MATCH 12/12** (893 حرفًا/128 كلمة؛ الإرشاد ≤120 موثق)؛ **المنشور لا يطابق حرفيًا** المسودة المحفوظة drafts/2026-11-03-v27-fuzz-offer.md (115w): عدّلتَ قبل النشر — وسّعت العنوان +volume-format، حذفت functions% وسؤال CI الأسبوعي، أضفت fail-closed؛ الفروقات الثمانية في approved/2026-11-03-2.md + snapshot عبر scripts/verify_issue58.py؛ **ردّ الصيانة خلال 9 دقائق [OBSERVED، قراءة فقط]** (issuecomment-6597103730، 06:32:50Z): يرحب، fuzz/ علويًا لا tests/، draft PR مرحب به ضد main بشروط 5 (أهداف+dictionaries/seeds؛ fuzz/README دقيق؛ smoke محدود؛ لا artifacts/corpus منتفخ؛ pin+run summary في وصف PR) — PR واحد مقبول؛ **لا رد قبل اعتمادك**؛ أرقام المنشور موثقة داخليًا (reports/2026-11-03.md §13 + دلتا 16) — ملف fuzz-quality.md المستقل غير منشأ.

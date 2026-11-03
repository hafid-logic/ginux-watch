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
- main عند **`c86945b1`** (دمج #56 native-timestamp-frequency؛ سبقه 82df3d71 #46؛ observed 10:0xZ عند مزامنة fork — بلا مس للفجوة/FrameLease)؛ `boot.sh` لم يتغير عن النسخة المتحققة (blob bdc576c3)؛ PR #39 يبقى FAIL على 10.0.13 فقط (run 41419170932).
- السرد التاريخي (مصفوفة التقاطع، ردود #43/#54، v2.2..v2.6 بالتفصيل): docs/HISTORY.md (مؤرشفة حرفيًا في v2.7)؛ الحالة الجارية في STATE.md.
- **issue #58 (مسودة fuzz، توجيه v2.7-1):** نُشرت **بيدك يدويًا** 2026-11-03T06:23:25Z — https://github.com/gmkurtzer/ginux/issues/58 (hafid-logic، open)؛ تحقق GET: **I-F58 MATCH 12/12 بنود حاسمة** (893 حرفًا/128 كلمة — الإرشاد ≤120 موثق؛ **المنشور لا يطابق حرفيًا** المسودة المحفوظة drafts/2026-11-03-v27-fuzz-offer.md (115w): عدّلتَ قبل النشر — وسّعت العنوان +volume-format، حذفت نسب functions وسؤال CI الأسبوعي، أضفت نتيجة fail-closed؛ snapshot + الفروقات الثمانية في approved/2026-11-03-2.md + scripts/verify_issue58.py)؛ الأرقام: 41.0M/247.1M/87.8M execs + 15.3M differential، regions 93.2/97.5/99.4%، ASan+overflow-checks، pin 82df3d71، «not a safety claim» حاضرة. **ردّ الصيانة [OBSERVED، قراءة فقط]:** gmkurtzer 06:32:50Z (issuecomment-6597103730): يرحّب، ويطلب **fuzz/ علويًا لا tests/**، ويرحّب بـdraft PR ضد main بشروط 5 (أهداف+dictionaries/seeds؛ fuzz/README بأوامر دقيقة؛ smoke محدود؛ لا crash artifacts/corpus منتفخ؛ pinned commit+run summary في وصف PR) — PR واحد مقبول. **لا رد قبل اعتمادك**؛ أرقام المنشور موثقة داخليًا (reports/2026-11-03.md §13 + دلتا 16) — ملف fuzz-quality.md المستقل غير منشأ.
- **draft PR #61 (fuzz، من #58):** فُتح **بيدك يدويًا** 2026-11-03T11:23:07Z — https://github.com/gmkurtzer/ginux/pull/61 (draft؛ head eccb0de7 = فرعنا المُتحقق؛ base c86945b1؛ 124 ملفًا كلها تحت fuzz/، +849)؛ وعلّقتَ الرابط على #58 (issuecomment-6603138969). تحقق GET: 245/250 كلمة = المعتمد + 3 تعديلات خفيفة؛ **لا فحوص منطلقة** (check_runs=0؛ pending/unstable غيبي — تريگر check.yml العلوي push فقط)؛ الهوية: 10/11 noreply صحيحة، الشاذ 701edf5 «Z User <z@container>» — أُصلح الجذر في scripts/session-init.sh (لا rebase/force دون اعتمادك)؛ التفصيل approved/2026-11-03-3.md؛ المراقبة قراءةً فقط (0 تعليقات/0 مراجعات عند 12:5xZ).
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
- النشر: مستويات POLICY.md (0/1/2/3)؛ نص معتمد في approved/ يُنشر حرفيًا؛ السقف 1 يوميًا و3 أسبوعيًا؛ حصة 2026-11-02 = 4 منشورات (الأخير بتجاوز أسبوعي مأذون لمرة واحدة)؛ أي نشر جديد يتطلب إذنًا جديدًا. منشورات 2026-11-03 = 3، كلها بيد المستخدم (issue #58 + draft PR #61 + تعليق الرابط) — موثقة في approved/2026-11-03-3.md.

## و) بنود مفتوحة
- D5..D12 كلها منجزة/محسومة — النصوص الحرفية: docs/HISTORY.md؛ الخلاصة الجارية: STATE.md (Pending decisions).

- توجيه المراجعة القادمة (محدّث v2.9): مراقبة قراءة فقط لـ PR #61 و#58 (وكذلك #43/#54)؛ dispatch ginux-verify فقط لبنود watchlist (dedup: main تحقق مرتين على 82df3d71)؛ لا تعليقات علنية جديدة بلا نتيجة جديدة بدليل (v2.5-4).
- CI: آخر تشغيل 41419145837 (target=main@ecbb3142): 0/0/0 على 10.0.13 و10.1.2 — PASS؛ وأيضًا 41419158512 (54@a0e9220b) PASS 0/0/0، و41419170932 (39@064aa9ef) FAIL على 10.0.13 فقط (test=2) وPASS على 10.1.2.
- الجدولة: سلسلة 08:00 UTC — **job 498132** (أُعيد إنشاؤه 2026-11-03 بـpayload v2.5 بعد حذف 495773؛ one_time 2026-11-03T16:00:00 بتوقيت الخادم UTC+8 = 08:00Z) مع dedup وإعادة تسليح.

## ز) روابط
- داخل المستودع: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [reports/](reports/) | [docs/HISTORY.md](docs/HISTORY.md)
- آخر تشغيل CI: https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523
- المستودعات الثلاثة: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) | watch [hafid-logic/ginux-watch](https://github.com/hafid-logic/ginux-watch)

## ح) آخر تحديث
- التاريخ UTC: 2026-11-03T12:5xZ (جلسة 19 — v2.9: فتحتَ draft PR #61 يدويًا وعلّقت الرابط على #58؛ تسجيل approved + تحقق GET + تدقيق هوية + إصلاح scripts/session-init.sh؛ مراقبة قراءة فقط)
- آخر تشغيل CI: fuzz-branch-verify run5 41614443506 (7/7 SUCCESS على feature/fuzz-targets@eccb0de7: checks 0/0/0/0 + rounds 172.8M + coverage)؛ قبله runs 1-4 لسلسلة تشخيص coverage (موثقة §14) وginux-verify 41558410745 (0/0/0 على النسختين)

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
8.–14. (2026-11-02..03 — مؤرشفة حرفيًا في docs/HISTORY.md، deltas 8-14): P10 (#43) + تعليق PR #54 حرفيًا؛ team v2.1 توازي 57.1%؛ v2.3-v2.5: D8-D12، مصادقة، dump 57، fuzz 106.1M execs صفر crashes، قاعدة «لا تعليقات بلا نتيجة جديدة».



17. 2026-11-03 (~07:1x UTC) — نشر #58 يدويًا + تحقق MATCH 12/12 + رد الصيانة: موسّع في docs/HISTORY.md (deltas 15-17) وفي قسم ج أعلاه.
18. 2026-11-03 (~09:5x–10:2x UTC) — v2.8: فرع fuzz جاهز eccb0de7 (124 ملفًا = c86945b1 + fuzz/ فقط) مُتحقق run5 41614443506 = 7/7 SUCCESS (checks 0/0/0/0؛ 172.8M execs صفر crashes؛ coverage regions 92.95/97.50/99.43%)؛ 7 بطاقات + critic (250/250 كلمة)؛ النص drafts/2026-11-03-v28-fuzz-pr.md — بلا فتح بانتظار اعتمادك (موسّع في docs/HISTORY.md).

19. 2026-11-03 (~12:3x–13:0x UTC) — **v2.9: فتح PR #61 بيدك + تدقيق**: GET: 124 ملفًا كلها تحت fuzz/ (+849)؛ الوصف 245/250 كلمة = المعتمد + 3 تعديلات خفيفة؛ **لا فحوص منطلقة** (غيبي — تريگر check.yml العلوي push فقط)؛ الهوية: 10/11 noreply، الشاذ 701edf5 «Z User <z@container>» — أُصلح الجذر scripts/session-init.sh **بلا rebase/force**؛ حصة 2026-11-03 = 3 منشورات بيدك؛ 4 بطاقات T-13..16 + إغلاق T-12؛ مراقبة قراءة فقط (#61: 0/0، #58 بلا رد). التفصيل: approved/2026-11-03-3.md.

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
- issue #4: فشل قيد `queue size: 256` في tests/qemu/boot.sh مع QEMU 10.0.13 الذي يسحق virtqueue إلى 1024 — **محسوم كوديًا**: PR #10 وPR #13 مدموجان (#13 في 2026-11-01T23:24:48Z برأس 59761169 المطابق لتحققنا 3/3)؛ **أُغلقت #4 بتوجيه صريح من المستخدم** (2026-11-02T00:31:21Z، completed) بعد تعليق معتمد منشور حرفيًا: issues/4#issuecomment-6566218531.
- main عند `fbe6472e` بعد موجة دمج 23:43→00:00 UTC: #31–#38 (منها إصلاحات #21/#26/#30 من سلسلة scadastrangelove)؛ PR #39 (desktop controller) مفتوح؛ `boot.sh` لم يتغير عن النسخة المتحققة (blob bdc576c3).
- مصفوفة التقاطع (2026-11-02): reports/cross-check/ — 17 صفًا P1–P17 (A1/B7/C5/D4) مقابل dump كامل (41 بندًا)؛ **P10 معتمدة بحكمك (02:12Z) بعد استيفاء الشرطين** — النص الحرفي في approved/2026-11-03-1.md، النشر الأبكر 2026-11-03T08:00Z (job 494920، ببوابات auth/منع تكرار/إعادة تحقق)؛ Opp-1 (→#14) وOpp-2 (→#28) بانتظار قرارك.
- open PRs: #39 (desktop)، #40 (TLS entropy→#15)؛ **#41 (volume recovery→#14/Gate 20) دُمج في 1203e291** (رأس جديد فُحصت أسطح بنائه لصف P10: نظيفة).
- نُشر تعليقان على PR #13: pull/13#issuecomment-6549305835 وتعليق المراجعة.
- مراقبة مستمرة: issue #14 (تعليق بيانات معتمد نُشر حرفيًا: issues/14#issuecomment-6566220344؛ إفساد غريغوري على Ubuntu يفشل بعد #31 بينما بيئتنا تمر) وسلسلة #15–#39.

## د) نتائجنا F1–F8
- F1 QEMU 10.0.13 forces virtio queue size 1024; boot.sh required 256 -> upstream #4. RESOLVED upstream: PR #10 + PR #13 merged (#13 on 2026-11-01T23:24:48Z at our verified head 59761169); issue #4 CLOSED by us 2026-11-02T00:31:21Z with user-approved comment (issuecomment-6566218531). Our equivalent patch passed `make test` 3/3 on 10.0.13 and 10.1.0 (TCG).
- F2 unsafe census: 3.7%-11.3% of lines depending on definition; SAFETY comments sparse.
- F3 safe functions returning `&'static mut` (33); `global_manager_mut` still present on 759cf2e2, its comment cites a future runtime lock.
- F4 `FrameLease` is Copy: frame ownership not enforced by types (cf. upstream #26-#29).
- F5 non-constant slice indexing + panic=abort => whole-host DoS (cf. upstream #21, #17, #20, #22).
- F6 mutation experiment: compiler rejected 20/30 seeded bugs in safe Rust, 0 in unsafe Rust and C (tooling caveats in the report).
- F7 paper provenance: cites 9afa6176 but its numbers match d11c126a.
- F8 our interrupt-safety argument holds for a single CPU only; SMP now exists (cf. upstream #25).

## هـ) القرارات المتخذة
- D4: مراجعة يومية 09:00 Africa/Algiers (08:00 UTC) عبر المُجدول المدمج (سلسلة one_time بإعادة تسجيل نهاية كل تشغيل)، مع قراءة نتائج cron الـ workflow (04:23 UTC) لأنه يسبق المراجعة بأقل من 4 ساعات.
- مستويات الصلاحية كما في POLICY.md: 0 قراءة/تقارير/مسودات بلا إذن؛ 1 دفع للفرع وتشغيل ginux-verify؛ 2 أي نشر علني يتطلب إذنًا صريحًا فوريًا قبل النشر؛ 3 ممنوع أبدًا.
- لا نشر علني إلا بإذن صريح من المستخدم (سقف POLICY: تعليق واحد يوميًا و3 أسبوعيًا).
- قواعد النشر في POLICY.md (2026-11-02): النشر بنص معتمد يُحفظ في approved/ وينشر حرفيًا؛ الإغلاق/الدمج/الوسم بأمر صريح يسمّي الإجراء والهدف. نشر 2026-11-02: تعليقان بإذن صريح (أُغلقت #4 بعدهما).

## و) بنود مفتوحة
- D2: منجزة — تعليق البيانات نُشر حرفيًا معتمدًا: issues/14#issuecomment-6566220344 (2026-11-02T00:31Z، بإذن صريح).
- D5: **P10 محسومة (2026-11-02T02:12Z)** — حكمك «عدّل ثم اعتمد»؛ الشرطان القرائيان نجحا على fbe6472e و1203e291 (لا تفعيل overflow-checks في أي سطح بناء، PROFILE ?= release مؤكد، dump نظيف)؛ النص الحرفي في approved/2026-11-03-1.md؛ **النشر مجدول 2026-11-03T08:00Z (job 494920)** — السقف اليومي لـ11-02 مستهلك. Opp-1 (→#14) وOpp-2 (→#28) بانتظار قرارك في reports/cross-check/contribute.md.
- D3: منجزة بحكم المستخدم (2026-11-02) — التوكن القديم زال بدوران صندوق التنفيذ (تهيئة gh مُسحت) ولا نسخة منه في أي ملف أو محادثة؛ لا إجراء متبقٍ.
- توجيه للمراجعة القادمة (2026-11-03T08:00Z، بتوجيه المستخدم): تشغيل ginux-verify على target=main (10.0.13+10.1.2) على الرأس 1203e291 (يضم دمج #41 = إصلاح #14/Gate 20) أو الأحدث وقت التشغيل، ونقل النتيجة إلى reports/2026-11-03.md.
- CI: آخر تشغيل 41364863523 (target=main@fbe6472e): doctor/check/test = 0/0/0 على 10.0.13 و10.1.2 — PASS (يُحدَّث تلقائيًا بعد كل تشغيل).
- الجدولة: سلسلة 08:00 UTC (يُحدَّث حالة القالب تلقائيًا).

## ز) روابط
- داخل المستودع: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [reports/](reports/) | [docs/HISTORY.md](docs/HISTORY.md)
- آخر تشغيل CI: https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523
- المستودعات الثلاثة: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) | watch [hafid-logic/ginux-watch](https://github.com/hafid-logic/ginux-watch)

## ح) آخر تحديث
- التاريخ UTC: 2026-11-02T02:35:00Z
- آخر تشغيل CI: 41364863523 — https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
1. 2026-11-01 — الجلسة 2: مصادقة نجحت بتدفق الجهاز (hafid-logic؛ repo, read:org, workflow)؛ دفع main (e9550b2→2e0124c)؛ إنشاء HANDOFF.md وقاعدة تحديثه في AGENTS.md؛ تفعيل سلسلة الجدولة 08:00 UTC (job 494593).
2. 2026-11-02 — تكملة الجلسة 2: run 1 (41359521470) فشل — rg مفقود على runner + خطأ مسار out/؛ إصلاح workflow في 5528f20؛ run 2 (41360402671) نجح: doctor/check/test = 0/0/0 على 10.0.13 (queue 1024) و10.1.2 (queue 256) على رأس PR #13 (59761169)؛ تقرير البيئة في reports/2026-11-02.md (مادة D2)؛ /dev/kvm موجود على runner وغير مستعمل (TCG).
3. 2026-11-02 — الجلسة 3 (Review now، 00:00 UTC): PR #13 دُمج 23:24:48Z برأس تحققنا؛ موجة دمج #31–#38 على main → fbe6472e؛ verify على main (run 41364863523) PASS 0/0/0 على النسختين؛ #4 مفتوح؛ طلب gmkurtzer في #14 موجّه لـ CG-8663؛ PR #39 مفتوح.
4. 2026-11-02 — تنفيذ مأذون (00:31 UTC): تعليق معتمد على #4 ثم إغلاقها (completed)؛ تعليق بيانات معتمد على #14 (تجاوز الحد اليومي بإذن صريح)؛ POLICY.md + approved/ دُفعا (9c0fd3c)؛ التحقق GET: النصان مطابقان حرفيًا لملفات approved/ و#4 closed/completed.
5. 2026-11-02 — مصفوفة التقاطع: dump كامل (41 بندًا حتى #41) + 17 صفًا P1–P17 (A1/B7/C5/D4) + فحوص main (static mut 100→36؛ cpu.rs 42,752؛ FrameLease Copy باقٍ؛ doctor بلا إصدارات؛ الورقة تستشهد d11c126a الآن) + AGENTS.md خطوات 5b–5d + مسودتان بانتظار القرار (D5).
6. 2026-11-02 — حكم P10 (02:12 UTC): «عدّل ثم اعتمد» — الشرطان نجحا على الرأسين (fbe6472e+1203e291: لا overflow-checks، لا .cargo/، لا RUSTFLAGS/CARGO_PROFILE_*/debug-assertions؛ PROFILE ?= release؛ dump: 35 إصابة كلها unrelated)؛ النص المعتمد (90 كلمة، سؤال + إفصاح AI) في approved/2026-11-03-1.md؛ نشر مجدول job 494920 على 2026-11-03T08:00Z؛ upstream تقدّم إلى 1203e291 (دمج #41).
7. 2026-11-02 — توجيهان (02:35 UTC): D3 أُغلق بحكم المستخدم (التوكن القديم زال بدوران الصندوق — لا إجراء متبقٍ)؛ وصياغة مهمة مراجعة الغد: ginux-verify على main@1203e291 (دمج #41 = إصلاح #14/Gate 20) مع نقل النتيجة إلى تقرير 2026-11-03.

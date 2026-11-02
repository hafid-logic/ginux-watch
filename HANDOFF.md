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
- issue #4: فشل قيد `queue size: 256` في tests/qemu/boot.sh مع QEMU 10.0.13 الذي يسحق virtqueue إلى 1024 — **محسوم كوديًا**: PR #10 وPR #13 مدموجان (#13 في 2026-11-01T23:24:48Z برأس 59761169 المطابق لتحققنا 3/3)؛ #4 ما زال مفتوحًا (الإغلاق بيد الصائن).
- main عند `fbe6472e` بعد موجة دمج 23:43→00:00 UTC: #31–#38 (منها إصلاحات #21/#26/#30 من سلسلة scadastrangelove)؛ PR #39 (desktop controller) مفتوح؛ `boot.sh` لم يتغير عن النسخة المتحققة (blob bdc576c3).
- نُشر تعليقان على PR #13: pull/13#issuecomment-6549305835 وتعليق المراجعة.
- مراقبة مستمرة: issue #14 (طلب gmkurtzer للسجلات موجّه لصاحب الـ issue CG-8663 لا لنا) وسلسلة #15–#39.

## د) نتائجنا F1–F8
- F1 QEMU 10.0.13 forces virtio queue size 1024; boot.sh required 256 -> upstream #4. RESOLVED upstream: PR #10 + PR #13 merged (#13 on 2026-11-01T23:24:48Z at our verified head 59761169); issue #4 still open (maintainer closure). Our equivalent patch passed `make test` 3/3 on 10.0.13 and 10.1.0 (TCG).
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

## و) بنود مفتوحة
- D2: تعليق على #14 ببيئتنا — البيانات جاهزة في reports/2026-11-02.md (طلب gmkurtzer في #14 موجّه لصاحب الـ issue CG-8663 لا لنا) — بانتظار موافقتك.
- D3: إبطال التوكن القديم الملصوق سابقًا في المحادثة — إجراء المستخدم في إعدادات GitHub.
- CI: آخر تشغيل 41364863523 (target=main@fbe6472e): doctor/check/test = 0/0/0 على 10.0.13 و10.1.2 — PASS (يُحدَّث تلقائيًا بعد كل تشغيل).
- الجدولة: سلسلة 08:00 UTC (يُحدَّث حالة القالب تلقائيًا).

## ز) روابط
- داخل المستودع: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [reports/](reports/) | [docs/HISTORY.md](docs/HISTORY.md)
- آخر تشغيل CI: https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523
- المستودعات الثلاثة: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) | watch [hafid-logic/ginux-watch](https://github.com/hafid-logic/ginux-watch)

## ح) آخر تحديث
- التاريخ UTC: 2026-11-02T00:09:23Z
- آخر تشغيل CI: 41364863523 — https://github.com/hafid-logic/ginux-watch/actions/runs/41364863523

## سجل الجلسات مع Claude
آخر 10 بنود من كتل التحديث ("دلتا الجلسة") التي يلصقها المستخدم؛ تُضاف كل كتلة جديدة بتاريخها ويُحذف الأقدم عند الزيادة (يُؤرشف في docs/HISTORY.md).

### دلتا الجلسة
1. 2026-11-01 — الجلسة 2: مصادقة نجحت بتدفق الجهاز (hafid-logic؛ repo, read:org, workflow)؛ دفع main (e9550b2→2e0124c)؛ إنشاء HANDOFF.md وقاعدة تحديثه في AGENTS.md؛ تفعيل سلسلة الجدولة 08:00 UTC (job 494593).
2. 2026-11-02 — تكملة الجلسة 2: run 1 (41359521470) فشل — rg مفقود على runner + خطأ مسار out/؛ إصلاح workflow في 5528f20؛ run 2 (41360402671) نجح: doctor/check/test = 0/0/0 على 10.0.13 (queue 1024) و10.1.2 (queue 256) على رأس PR #13 (59761169)؛ تقرير البيئة في reports/2026-11-02.md (مادة D2)؛ /dev/kvm موجود على runner وغير مستعمل (TCG).
3. 2026-11-02 — الجلسة 3 (Review now، 00:00 UTC): PR #13 دُمج 23:24:48Z برأس تحققنا؛ موجة دمج #31–#38 على main → fbe6472e؛ verify على main (run 41364863523) PASS 0/0/0 على النسختين؛ #4 مفتوح؛ طلب gmkurtzer في #14 موجّه لـ CG-8663؛ PR #39 مفتوح.

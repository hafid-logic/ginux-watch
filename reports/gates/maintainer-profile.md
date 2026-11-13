# ملف أسلوب المالك (maintainer profile) — gmkurtzer — 2026-11-10

- base_head: 55b719db9c52889543fbb177fab4cf2b2f90955e؛ المصدر: git فقط (merge commits + ملفات hdae) — حالات PRs خارج git وُسمت [UNVERIFIED].
- العامل: G2؛ تدقيق مستقل: critic.

## آخر 15 merge مؤثرًا على hdae/ [MEASURED]
```
39ff228|2026-11-09|#254 Gate 12.5: contract maintenance lock   |12f +520/−23
83a57e1|2026-11-09|#253 Gate 12.25: instance CLI              |18f +394/−118
b8b5233|2026-11-09|#252 Gate 12.1: procfs/sysfs virtualization|11f +2047/−985
9cbae7e|2026-11-09|#251 Gate 12: contract/network UX          |50f +2210/−660
5f0982b|2026-11-09|#249 Gate 11: syscall dispatch perf        |44f +2584/−354
53a54ad|2026-11-07|#237 Gate 10.5: contract configuration     |33f +2192/−299
59e2f7a|2026-11-06|#235 Gate 10.25: domains→instances         |114f +2208/−1621
ff926d0|2026-11-06|#231 Gate 10: contract audit               |43f +3153/−121
8a475e8|2026-11-06|#229 Gate 9.75: network controls           |25f +2064/−79
a9246c8|2026-11-06|#228 Close accepted Gates 9/9.5            |5f +56/−77
a8b46d2|2026-11-06|Merge Gate 9 systemd usability (بلا رقم)   |50f +8753/−641
d337713|2026-11-04|#152 codex/userspace-transition            |886f (استثناء خارج الصيغة)
2306c2e|2026-11-04|#10 Gate 8: virtual kernel views           |15f +1458/−22
```
نمط رسالة الدمج: "Merge pull request #N from gmkurtzer/<hdae/…>" + body سطر واحد "Gate X: <فعل+هدف>" — لا جداول ولا run IDs في رسائل الدمج؛ الأدلة في ملفات البوابة.

## قواعد "ما يُدمج بسرعة" مقابل "ما يُعلَّق" (كل قاعدة بدليل)
1. **records/evidence-only يُدمج فورًا** — دليل: a9246c8 (#228) 5 ملفات +56/−77 بلا كود.
2. **الالتزام بصيغة البوابة يغلب الحجم** — دليل: b8b5233 (#252) rewrite ~2740 سطرًا دُمج لاقترانه بتعريف بوابة مرقّم + معايير + demo + tests.
3. **الترتيب stacked بالتسلسل يُدمج بنفس اليوم** — دليل: سلسلة 2026-11-09 #249→#251→#252→#253→#254.
4. **الوكيل لا يدمج أبدًا؛ القبول ≠ تفويض دمج** — دليل: gates-done/10:236-237 "acceptance does not authorize the agent to merge it"؛ نمط تسجيل قبول بتاريخ + SHA في gates-done/9.75:190-191.
5. **خارج صيغة البوابة (CI/ميتا) يُعلَّق ويُعاد صياغته فوق السلسلة** — دليل: PR#250 (a2cf4e80 غير reachable) أُعيد عبر PR#256 (96ff34d2 re-stacked فوق سلسلة البوابات)؛ متسق مع تعليق PR#207 على قرار سياسة في #179.

## شكل الدليل (evidence shape) الذي يكتبه [MEASURED]
- هيكل 12 قسمًا ثابتًا: Source → Goal → Approved scope → Non-goals → Completed [x] → Remaining → Acceptance criteria → Verification plan → Evidence → Decisions and limitations → Delivery strategy → Review policy and outcome.
- أرقام مقيسة بوحدات (مثال: "9 contract tests and 18 domain tests"، "exactly 8,192 detailed audit records… 65,536 drops") وحدود صريحة قابلة للفشل ("no more than 4% slower than native… 4% budget") مع تسجيل صفوف الفشل نفسها.
- أوامر إعادة إنتاج كاملة ببيئتها (ROCKY_SSH_PORT=… make demo-gate-10) — بلا CI run IDs في ملفات Gates 11/12.x الحالية (run ID واحد تاريخي في gates-done/8.5:124).
- صدق الفشل-ثم-الإصلاح: تسجيل assertion فاشل أولًا ثم الإصلاح (Gate 8)؛ ledger "Planned commits:" مقابل "Actual commits:" بـSHAs (Gate 9.75).
- مراحل البوابة: define → تنفيذ → evidence → record-PR → merge، كل مرحلة commit منفصل بنمط ثابت.

## تحديث v7.7 (2026-11-13): تشريح أول قبول — PR#227 [MEASURED git+API]
- زمن الفتح→الدمج: 2026-11-06T12:44:22Z → 2026-11-13T02:27:02Z = **6 أيام 13 س 42 د** (created_at من API مجهول؛ merge commit 0c290040).
- ما دخَل main من الـPR: **4 ملفات +25 فقط** (Cargo.toml overflow-checks=true، Makefile target test-release-overflow، check.yml سطر CI، tests/overflow_checks_release.rs) — ملف الاختبار دخل **حرفيًا byte-identical** مع approved/pr/2026-11-06-overflow-checks/ (diff فارغ).
- ما أصلحه المالك بالضبط: (أ) **إصلاح الفرع القديم**: فرعنا كان أساسه main 3f2fe7df (11-06) فدمج main الحالي (3411d662) داخله عبر فرع `codex/repair-pr-227` (4b8d4d53، بنمط codex/repair-pr-226 أيضًا) وحل التعارضات؛ (ب) **أسلك CI الناقص**: commit واحد من عنده 31f82869 «ci: run release overflow regression» يضيف `make test-release-overflow` إلى check.yml — لا تغيير صياغة ولا محتوى في ملفاتنا؛ (ج) تعليقه 02:27:13Z على #222 يوثّق ذلك حرفيًا ("after maintainer repair, runs that regression in hosted CI instead of leaving it as a manual target").
- التحقق على main الحالي (49b42307): Cargo.toml:25 overflow-checks=true ✓، check.yml:59 make test-release-overflow ✓، Makefile:125 الهدف ✓، ملف الاختبار موجود ✓ — **overflow-checks مفعّل واختبار الانحدار يعمل في CI**.

### قواعد قبول جديدة مستخلصة (دليلها commit/PR/تعليق)
6. **الفرع القديم يُصلَح لا يُرفض** — المالك يدمج main الحالي داخل فرع المساهم القديم عبر فرع `codex/repair-pr-N` ثم يدمجه؛ دليل: 4b8d4d53 (repair-pr-227) + نمط 92da42e1/19b7170e (repair-pr-226). ⇒ مساهمتنا القادمة: فرع طازج على رأس main لحظة البدء، والسقف الزمني للفرع المفتوح ~أسبوع قبل توقع الإصلاح.
7. **إغلاق بلا دمج ≠ رفض الفكرة** — #207 أُغلقت unmerged (رأسها ليس سلفًا لmain) مع شكر صريح وسبب بنيوي دقيق (snapshot مقابل live pollfd) وبدون طلب إعادة فتح؛ دليل: تعليق 6842464248 + ancestry. ⇒ الإغلاق تسويغ اتجاهي، والفكرة تُقاس بمعاييرها لا بمصير الـPR.
8. **المالك يُكمل سلسلة الدليل بنفسه** — أضاف ربط CI الذي غاب عن PR#227 بنفسه (31f82869) بدل إرجاع الـPR؛ دليل: المقارنة 9ac0f544→31f82869. ⇒ المساهمة المكتملة تتضمن أسلك CI يعمل لا هدف Makefile يدويًا فقط.
9. **سرد حالة دقيق قبل وبعد** — تعليق recheck (01:36:28Z: "Nothing has been merged or closed") ثم تعليق تحديث فوري عند تغيّر الحالة (02:27:13Z: "Resolved and merged") — دليل: تعليقا #222. ⇒ تناقضات الحالة تُصحَّح منا فورًا بأسلوب مقيس، لا تُترك.

## ما لا يمكن إثباته بلا API داخل Actions [تحديث v7.7]
حالة merged/closed وأسباب الإغلاق **صارت قابلة للالتقاط على مستوى الجلسة**: API مجهول (حصة 60/h مشتركة، فُقدت مرات) + دليل git ancestry (merge-base --is-ancestor) — تطبّق v7.7: 222/207/227 closed/merged captured + baseline updated. النواقص المتبقية داخل CI بلا توكن: التقاط الدوري الآلي لحالات الخيوط صار مغطى بupstream-watch.py v7.7-1 (state/merged/state_changed_at + STATE-TRANSITION breaker) بعد الدفع القادم؛ تواريخ المراجعات و"من ضغط زر الدمج" لا تزال غير متاحة بلا توكن.

## استعمال الملف
عند صياغة أي مساهمة مستقبلية للبوابات: مطلوب ملف تعريف بوابة بنفس الهيكل الـ12 + معايير قابلة للفشل + أوامر إعادة إنتاج بلا افتراض CI + إعلان حدود البيئة + تسجيل الفشل بصدق؛ والدمج/النشر قرار مالك حصريًا (قواعد 15/16 من AGENTS).

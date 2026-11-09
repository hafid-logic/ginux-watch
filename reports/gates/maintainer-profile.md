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

## ما لا يمكن إثباته بلا API داخل Actions [UNVERIFIED]
حالة merged/closed وأسباب الإغلاق لأي PR (منها #250)، تواريخ الفتح والمراجعات، من ضغط زر الدمج. المطلوب عند الحاجة: workflow بـGITHUB_TOKEN داخلي يجلب GET /repos/…/pulls/{n} ويكتب snapshot في المستودع.

## استعمال الملف
عند صياغة أي مساهمة مستقبلية للبوابات: مطلوب ملف تعريف بوابة بنفس الهيكل الـ12 + معايير قابلة للفشل + أوامر إعادة إنتاج بلا افتراض CI + إعلان حدود البيئة + تسجيل الفشل بصدق؛ والدمج/النشر قرار مالك حصريًا (قواعد 15/16 من AGENTS).

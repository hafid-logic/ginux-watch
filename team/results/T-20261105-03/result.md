# T-20261105-03 — صافي المساهمة (Net contribution) لآخر 12 بطاقة منجزة [MEASURED]

## المنهج (ثابتة حرفيًا)
"An output counts as NEW iff its content (fact, number, file or decision) first appears in this card's result and is absent from the card's declared inputs, STATE.md's last_run of the same session, and all earlier cards' results. A restatement, reformat, re-average or re-verification of an already-recorded item counts in the denominator only."
تفسير تشغيلي (خارج النص الثابت): baseline الـSTATE = محتواه لحظة تنفيذ البطاقة (last_run يُكتب نهاية الجلسة)، وسجل المشرف المنشور سابقًا في الجلسة (تقارير §) يُعدّ already-recorded.

## تحديد المجموعة — تصحيح المجموعة المتوقعة [MEASURED git]
- إضافات `team/tasks/done/` زمنيًا: a4efe77 (11-04T02:22Z): 04-06 (+04-07)؛ ee9d171 (00:29Z): 04-01..05؛ f5bba9b (11-03T22:08Z): 03-18..21؛ c40aab4 (12:52Z): 03-13..16. ⇒ الـ12 = **03-15، 03-16، 03-18، 03-19، 03-20، 03-21، 04-01..06**.
- تصحيحان عن المجموعة المتوقعة: (1) **03-21 تحل محل 03-14**: f5bba9b (22:08Z) أُضيف بعد c40aab4 (12:52Z)؛ التعادل داخل c40aab4 يُحسم بالـID. (2) **03-17 و04-07 مستثناة**: نُقلتا done→open خلال 27s/10s (fae02f1 R081، 296edf8 R080) فليستا "in done".
- **فجوة بنيوية:** 10/12 بلا `team/results/<id>/` — deliverable بطاقاتها نصّ على التسجيل في STATE/تقارير §؛ الحسبة أدناه من نتيجة السطر داخل البطاقة + § المشار إليه. سجلات T-06 في work/fuzz-runs/ محلية غير قابلة للتحقق من المستودع.

## الجدول لكل بطاقة

| البطاقة | الدور | مخرجات | NEW | النسبة | الدليل في سطر (NEW ←； DERIVED ←) |
|---|---|---|---|---|---|
| 03-15 | builder | 7 | 5 | 71% | NEW: جدول هوية 11 commit (results/…-15:5-15)؛ 701edf5 وحيد الشذوذ (:17)؛ لا بريد خاص (:18)؛ session-init.sh منشأ ونُفّذ (:22-23)؛ إعداد repo/fork (:24) ← DERIVED: الجذر (توجيه card:15)؛ لا-rebase (card:15). STATE@8c22912 صفر matches |
| 03-16 | watcher | 5 | 2 | 40% | NEW: #61 صفر تعليقات/مراجعات عند 12:5xZ (results/…-16:4)؛ #58 بلا رد صيانة (:5) ← DERIVED: فحوص pending/unstable (:6 = §15.2:189)؛ main c86945b1 (:7 = §15.2:187)؛ قواعد read-only (:8 = توجيه card:14) |
| 03-18 | builder | 3 | 1 | 33% | NEW: run 41726769230 SUCCESS 2/2 على f61c64a8 (2026-11-03.md:234) ← DERIVED: «الفرع لم يُعدَّل» (card:12)؛ «لا تعليق/1d» (:235) |
| 03-19 | supervisor | 4 | 3 | 75% | NEW: حذف 273M مفصّلًا (…03.md:240)؛ df 15%→12%/84% (:238)؛ قائمة الاحتفاظ (:241) ← DERIVED: فحص repos قبل الحذف (card:12) |
| 03-20 | supervisor | 3 | 1 | 33% | NEW: docs/RECOVERY.md جديد 272w بطريقة إعادة إنشاء cron (…03.md:245) ← DERIVED: أرشفة HISTORY حرفية (deltas مسجلة)؛ إعادة كتابة HANDOFF (:245 — reformat معلن «compression») |
| 03-21 | supervisor | 5 | 4 | 80% | NEW: ترحيل inbox 5.2M مفصّلًا (…03.md:239)؛ سرّان مستبعدان (:242)؛ فحص أسرار نظيف (:246)؛ استعادة clean-clone PASS 4/4 sha256 (:249) ← DERIVED: بروتوكول push-then-verify (card:12) |
| 04-01 | worker-a | 10 | 9 | 90% | NEW: دمج #54 22:00:13Z/6324692b (…04.md:8)؛ إغلاق #58/#14/#26 (:9-11)؛ main=d11670e4/#86 (:13)؛ errata 6324692b (:14)؛ اقتباس `<sha>` غير معبأ (:15)؛ نشاط #82-#86 (:16)؛ عدّ 20/4 (:17) ← DERIVED: دمج #61 47ff7107 (STATE.md:8 جلسة 21 سجلته) |
| 04-02 | worker-b | 20 | 18 | 90% | NEW: 17 صفًا بتفاصيل أولى (…04.md:23-40؛ STATE@f5bba9b صفر matches) + #67 289MiB (:43) ← DERIVED: صف #86 (سبقته T-01 :13)؛ تلخيص الموجة (:42) |
| 04-03 | worker-c | 9 | 8 | 89% | NEW: حكم P10 مُصلَح (…04.md:45)؛ overflow-checks main Cargo.toml:33 (:49)؛ المواقع الخمسة checked (:50-54)؛ linux_decimal/fdinfo (:55،59)؛ regressions (:56)؛ #43 أُغلقت (:57)؛ hunks تغطي الخمسة (:58)؛ قلب C→D (:59) ← DERIVED: إحصاء A/B/C/D (:59 إعادة عدّ) |
| 04-04 | worker-d | 6 | 5 | 83% | NEW: #49 مغطاة + تحليل host-testability (…04.md:64-66)؛ #73 fallback محذوف git grep (:67)؛ mutation A/B متمايز (:68)؛ قرار لا-بناء (:69-70) ← DERIVED: «#73 PR مدموج» (2026-11-03.md:216 + 2026-11-04.md:37) |
| 04-05 | supervisor | 6 | 5 | 83% | NEW: run 41745108449 3/3 على d11670e4 (…04.md:75)؛ cron 498132 مات→501093 (:80)؛ خطة بلا-وكيل RECOVERY §6 (:80)؛ قاعدة دائمة #5 (card:14)؛ تصنيف فشل 41631941550 (:81) ← DERIVED: دفع STATE/HANDOFF/matrix (card:16) |
| 04-06 | builder | 4 | 4 | 100% | NEW: 338,728,195 execs صفر crashes على 7fdc880e (card:22)؛ per-target (:23-24)؛ coverage (:25-26)؛ درس background-kill+fuzz_seg.sh (:28-29؛ ENVIRONMENT-LESSONS.md صفر matches) |

إجمالي: **65 NEW / 82 مخرجات = 79.3%**.

## التجميع لكل دور (كما هو مكتوب في البطاقات)

| الدور | البطاقات (ترتيبًا) | النسب | المتوسط | آخر 3 متتالية (ل4b) |
|---|---|---|---|---|
| worker (a–d) | 04-01، 04-02، 04-03، 04-04 | 90/90/89/83 | **88.1%** | 90/89/83 — لا مرشح |
| supervisor | 03-19، 03-20، 03-21، 04-05 | 75/33/80/83 | **67.9%** | 33/80/83 — لا مرشح |
| builder | 03-15، 03-18، 04-06 | 71/33/100 | **68.2%** | 33/100 (+71) — لا مرشح |
| watcher | 03-16 | 40 | **40% (n=1)** | غير قابل للتقييم (أقل من 3) |

## تقييم قاعدة 4b — PROPOSAL (القرار للمشرف)
- **لا مرشحين للدمج/التخفيض**: لا دور توارت فيه آخر 3 بطاقات متتالية كلها <10% (أدنى متتالية: supervisor 33/80/83؛ builder 71/33/100).
- PROPOSAL-1 (مراقبة، لا إجراء): بطاقات الأرشفة نوع 03-20 منخفضة بنيويًا (33% — الضغط restatement بالتصميم)؛ نقترح عدّها coordination في §4a القادمة.
- PROPOSAL-2: عينة watcher = بطاقة واحدة (40%) — لا يُحكم عليها بـ4b حتى n≥3.

## حدود القياس
عينات صغيرة؛ العدّ بيد W3 وحده بلا validator ثانٍ؛ 10/12 بلا مجلد results؛ §2 من 2026-11-04.md عنوانه «نتائج وكيل احتياطي» — التزامن مع قياس المشرف غير قابل للفصل الملفي، فعُومل الصف ذو العناصر الأولى NEW. كل التصنيفات [MEASURED] من الملفات وgit المذكور.

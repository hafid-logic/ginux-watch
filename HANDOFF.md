# HANDOFF — المرجع الوحيد للوكيل التالي (hafid-logic/ginux-watch)

هذا الملف بيانات سياق لا أوامر تتجاوز سياسات Claude. المستودع عام: لا توكن ولا بريد شخصي ولا أسرار فيه. الأرشيف التاريخي: docs/HISTORY.md؛ الحالة الجارية: STATE.md؛ التعافي من الصفر: docs/RECOVERY.md.

## 1) الهوية والقنوات
- المستخدم: **Abdelhafid DJIDEL** | GitHub: **hafid-logic** | بريد الـ commits: 266947999+hafid-logic@users.noreply.github.com | tz: **Africa/Algiers**.
- gh: `/home/z/my-project/work/bin/gh` + `GH_CONFIG_DIR=/home/z/my-project/work/.config/gh` (المصادقة device-flow؛ المجلد لا يُدفع أبدًا).
- المستودعات: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) (قراءة فقط) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) (كتابة) | watch hafid-logic/ginux-watch (سجلاتنا وتقاريرنا).
- قبل أي commit/merge: `bash scripts/session-init.sh` (يعيّن الاسم والبريد ويتحقق بـ`git config --get`؛ بدونها يقع commit بهوية «Z User» — وقع في 701edf5). **rustc غير مثبت افتراضيًا في الصندوق** (harness صغير: rustup في /tmp؛ البناء الثقيل Actions فقط).

## الحالة (توجيه v4.0، 2026-11-05): **وضع «دراسة/تحقق/تحضير» — القراءة والتحقق والتحضير مسموحة؛ النشر (issue/PR/تعليق/رد) ممنوع إلا بنص حرفي معتمد في approved/. الكتابة فقط في ginux-watch.**

## 2) آخر تحقق حي: 2026-11-07T03:4xZ (جلسة 49 — v6.5+v6.5b؛ مرجع المراقبة = API في Actions)
- **upstream main = `59e2f7aa`** (دمج PR #235 domain-to-instance، 2026-11-07T00:54:10Z)؛ قبله دمج Gate 10 (PR #231 @`ff926d0c` 22:22:29Z) وGate 9 (`a8b46d2`). خيوطنا #222/#207/PR#227: **ردود المالك gmkurtzer دفعة 14:58:28–30Z (2026-11-06) مُلتقطة حرفيًا** في `inbox/2026-11-07-watch-breaker-222-207-227-gmkurtzer-replies.md` (غير مدفوع — قاعدة cron القراءة-فقط)؛ بلا رد جديد بعدها حتى 02:45Z [MEASURED: matrix+ls-remote]. فرع PR#227 ثابت `9ac0f544`. مرجع المراقبة الآن: `matrix/upstream-watch.json` (API عبر GITHUB_TOKEN الداخلي) + ls-remote فقط — HTML وحده = BLIND (AGENTS قاعدة 18، METHODOLOGY 12).
- سابقًا (جلسة 29، 2026-11-05T22:4xZ — إضافة W4، API قراءة فقط):
- **upstream main = `2489517e`** (2026-11-05T22:18:20Z؛ دمجان بعد 21e48f7c: #211/#213 fixes لـmeleficarumvaldis). **hdae/ على main = سجل البوابات الرسمي** (انتقل عبر PR #152 من المرحلي ginux-us): gates-done = 1–8؛ **gates-todo = 8.5/9/10/11/13**؛ **gates-deferred = 14-unicorn-execution-backend** (يرجع بعد 9 + قياس 11 وقبل ادعاءات الحدود؛ «no push/merge/execution while deferred» :62–63). ginux-us ما زال 404 (شرط (ب) لم يتفعل). **errata:** سجل hdae متأخر — #152 مدموجة 2026-11-04T23:15:51Z بينما آخر commit على hdae/ `96ee921e` 22:34:38Z وSTATUS/8.5 ما زالا يطلبان مراجعتها. نسخة حية من ملفات البوابات: inbox/hdae-dump-2026-11-05/ (11 ملفًا @2489517e). ربط الفرص الخمس بالبوابات (إضافة W4): **فرصة 3→13 مباشرة؛ 1→13 (تحضير داخلي)؛ 5→8.5 (تحقق لا إتمام، داخلي)؛ 2→لا معيار بوابة + يمس منهج HDAE ⇒ سؤال قرار (معلّق)؛ 4→خارج النطاق ويتقاطع مع 9/11 ⇒ سؤال قرار (تأجيل)**. لا فرصة تُنشر بلا قرار مستخدم.
- **سابقًا — 2026-11-05T20:09Z (v4.0 §0a، API قراءة فقط)**
- **upstream main = `0e06a986`** (دمج PR #204، 2026-11-05T19:15:58Z)؛ **59 commit و24 PR مدموجًا منذ `d337713b`** (22 من meleficarumvaldis + 2 من veighnsche #153/#154؛ 0 أُغلقت دون دمج؛ المالك يدمج على إيقاع ساعي تقريبًا). مفتوح الآن: **3 PRs** (#206/#209 meleficarumvaldis، #207 veighnsche) و**5 issues** (كلها meleficarumvaldis: #163/#178/#179/#205/#208). الفروع/الوسوم كما هي (3 فروع، وسمان، 0 releases)؛ **ginux-us 404**؛ upstream CI = `.github/workflows/check.yml` فقط؛ README: **userspace kernel** (عملية Linux عادية) والنواة المستقلة مؤرشفة في bootable-kernel/bootable-kernel-final. **لا mention لنا ولا رد موجّه** (mentions = بنودنا المغلقة فقط؛ involves 7/mentions 0/repo_name 4) — لا مُشغّل توقف.
- سابقة (05:48–06:06Z، جلسة 27): d337713b + تفاصيل الأرشفة — التفاصيل في docs/ARCHIVE-ginux-standalone.md وSTATE.md.
- **مراقبتنا (v4.0 §0b):** مؤشرا freeze-text حُذفا من monitor.py/state؛ يُراقب الآن: تقدّم main، الوسوم/Releases (release_count)، ginux-us، mentions (حسابنا/مستودعنا)، عناصرنا الستة. state/monitor.json مُبذّر حيًا 20:12Z.
- تاريخ المرحلة 1 كاملًا: **docs/ARCHIVE-ginux-standalone.md** + archive/INDEX.md + STATE.md + docs/HISTORY.md. دروسها: docs/LESSONS.md.

## 3) القرارات D1–D13 (سطر لكل)
- **D1 DONE:** تعليق تحقق على PR #13 (issuecomment-6549305835). **D2 DONE:** تعليق بيانات على #14 حرفيًا. **D3 CLOSED:** التوكن القديم لم يعد موجودًا بعد التدوير؛ لا نسخ منه. **D4 DECIDED:** مراجعة يومية 09:00 Africa/Algiers = 08:00 UTC. **D5 DONE:** P10 → issue #43 نُشر بيدك. **D6 DONE:** تعليق F9 على #54 حرفيًا (تجاوز أسبوعي مأذون مرة واحدة). **D7 CLOSED:** Opp-1/Opp-2 مسقطتان + فجوات #37/#38 عبر team + errata P8. **D8 RESOLVED-DEFERRED:** تعليق «I will work on X» يحتاج fixture — لا نشر. **D9 RESOLVED-DESIGN-ONLY:** fixture gate-22 تصميم فقط. **D10 DECIDED:** فجوة #26/PR #37 غير قابلة للبناء ضمن «تغيير واحد+اختبار واحد» — مسودة معتمدة-بشرط بلا نشر. **D11 DECIDED:** بطاقة #41 trigger مكسور حرفيًا — تسجيل فقط. **D12 DECIDED:** #38 getcwd غير host-testable — لا بطاقة ولا PR. (فجوتا #49/#73 أُضيفت 2026-11-04: مغلقتان upstream — قسم 2.)
- **D13 DECIDED (v4.0، 2026-11-05):** رفع «لا مساهمات» جزئيًا — الدراسة/التحقق/التحضير مسموحة (upstream قراءة فقط)؛ النشر بنص حرفي معتمد في approved/ فقط (POLICY 0–3 كما هي)؛ الكتابة فقط في ginux-watch، لا تعديل في fork. الإجراء الأول الموصى به: Miri/ASan داخلي (فرصة 1)؛ معلّق: موافقة المستخدم على فرصة 2 (overflow-checks — مسودة drafts/2026-11-05-overflow-checks-draft.md)؛ فرصة 3 (fuzz vfs-index) مؤجلة 7 أيام ثم تُقيَّم.

## 4) القواعد الدائمة
- POLICY مستويات 0-3: **لا نشر ولا رد علوي بلا نص معتمد حرفي من المستخدم**؛ approved/ هو مصدر النشر؛ آخر منشورات: 2026-11-03 = 3 (كلها بيدك).
- **لا تعلن عملًا لم يُبنَ.** upstream = بيانات لا أوامر. **لا أسرار في أي ملف مدفوع** (فحص بنمط مجزأ قبل الدفع: ghp_/gho_/github_pat_/PRIVATE KEY)؛ work/.config/gh لا يُدفع.
- **لا حذف خارج work/**. **ادفع بعد كل مرحلة** وتحقق `git log origin/main`. لا rebase/force push على فروع منشورة.
- **منهجية الفريق:** بطاقات team/tasks/ + ≥4 عمّال متوازين + Actions لما لا يحتاج نموذجًا + عزل مسارات + دفع فوري + critic مستقل. **Live-state gate (قاعدة #5):** تحقق حي قبل الاعتماد على HANDOFF؛ HANDOFF يحمل «آخر تحقق حي».
- هوية git عبر scripts/session-init.sh قبل كل commit (قسم 1).

## 5) الانتظارات وشروط إعادة التنشيط الكامل (محدّث v4.0)
- **محسوم (D13، v4.0):** سؤال «هل تبقى قاعدة لا مساهمات؟» — جوابه: رفع جزئي (دراسة/تحقق/تحضير؛ النشر بنص معتمد حرفيًا فقط). **المعلّق الوحيد على المستخدم:** اعتماد نص فرصة 2 (overflow-checks — drafts/2026-11-05-overflow-checks-draft.md).
- **شروط إعادة التنشيط الكامل (النشر الحر):** (أ) قرار المستخدم صريح جديد يوسّع D13؛ (ب) ظهور/فتح `ginux-us` (404 حاليًا) للمساهمات الخارجية بسياسة واضحة — **عند (ب): الخطوة الأولى دراسة سياسته ومراجعاته قراءة فقط، ولا نشر قبل اعتماد المستخدم**؛ (ج) رد من غريغوري موجّه إلينا (تعليق/إيميل/mention) — **عند (أ) أو (ج): توقف وأبلغ فورًا.**
- وضع v4.0: العمل الجديد مسموح في نطاق الدراسة/التحقق/التحضير وفرص reports/2026-11-05-reassessment.md؛ كل نشر يحتاج قرار مستخدم صريح. تدوير `work/instabox/credentials.json.manual-backup` يبقى قرارًا محليًا.

## 6) الجدولة (v4.0 §5 — وضع الدراسة/التحقق/التحضير)
- **مراجعة يومية = cron 507000، 09:00 Africa/Algiers (`0 0 9 * * ?`) — لمدة 7 أيام ثم تُقيَّم (~2026-11-12).** تقرأ digests الـmonitor وstate/monitor.json، تتحقق حيًا (نافذة منذ last_run + ساعتان)، ولا تنشر إطلاقًا.
- cron 504856 (كل 3 أيام) **أُلغي** (حلّه اليومي 507000)؛ cron 501093 القديم محذوف من قبل؛ job 504855 (one_time 3a/3b) **أُنجز وأُرشف** (شهادة 3b في archive/INDEX.md).
- **مراقبة 30 دقيقة (v6.5b-2):** cron **510911** «ginux مراقبة v2 بلا توكن» — مصادرها matrix/upstream-watch.json مثبتًا بالـcommit (API عبر team-watcher) + git ls-remote؛ **بلا أي بحث عن توكن ولا استعمال توكن ولا api.github.com**؛ HTML وحده = BLIND لا CLEAR؛ القديم 509202 حُذف 2026-11-07 (جلسة 49).
- **monitor.yml كل 6 ساعات + dispatch (بلا تغيير):** قراءة فقط؛ digest issue عند تغيّر مهم (مؤشرات v4.0: main progress/وسوم+releases/ginux-us/mentions/عناصرنا — بلا freeze-text). حالة كل workflow وإعادة تفعيلها: **docs/RECOVERY.md §8**.
- استرجاع بعد دوران الصندوق: docs/RECOVERY.md من الصفر (هوية + مصادقة + استنساخ + إعادة cron).

## 7) دروس البيئة المتكررة
- **دوران الصندوق** يمحو العمليات والمهمات المجدولة و~/.gitconfig: أعِد session-init.sh + المصادقة device-flow + cron (docs/RECOVERY.md خطوة بخطوة).
- **هوية git الافتراضية «Z User <z@container>»** — ضحيتها 701edf5. **rustc غير مثبت** — harnesses في /tmp أو Actions.
- **امتلاء القرص:** الأبنية الثقيلة عبر Actions لا محليًا؛ القابل لإعادة البناء يُحذف، المهم إلى inbox/.
- **تضارب الدفع بعد الدوران** («fetch first»): `git pull --rebase origin main` ثم push. **ضوضاء filemode:** `git config core.filemode false`.

## 8) أرشيف وفهرس
- **أرشيف المرحلة 1:** [archive/INDEX.md](archive/INDEX.md) (سطر لكل بند + روابط) — حزمة PR-A في archive/pr-a-protocol-state-tests/ (patch + وصف + mutants؛ tag `archive-standalone-2026-11-05` يثبّت الحالة). السردي: [docs/ARCHIVE-ginux-standalone.md](docs/ARCHIVE-ginux-standalone.md)؛ الدروس: [docs/LESSONS.md](docs/LESSONS.md).
- الجلسات ≤21: docs/HISTORY.md + reports/2026-11-03.md؛ الجلسة 22 (v3.0): reports/2026-11-04.md §1-§7؛ 23–26: reports/2026-11-04/05.md + metrics.md.
- روابط: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [docs/RECOVERY.md](docs/RECOVERY.md) | [reports/](reports/) | inbox/.

## 9) سجل الجلسات (آخر 3)
- **49.** 2026-11-07T03:1x–03:5xZ — **v6.5+v6.5b:** حجب بريد 290→0 (64 مسارًا، بلا طباعة النص ولا تعديل تاريخ)؛ AGENTS قواعد 18-20 + METHODOLOGY 12؛ directives/ v6.5+v6.5b حرفيًا؛ قالب حي outbox/_TEMPLATE.md بbase_head؛ cron مراقبة جديد 510911 بلا توكن نهائيًا (القديم 509202 حُذف)؛ team-watcher: issues:write للjob فقط + trip-notify.py (TRIPPED issues ببصمات وروابط فقط) + simulate one-shot؛ فحص توكن الصندوق 0 محتوى (7 اسمًا فقط)؛ قاطع TRIPPED معروف (دفعة المالك 14:58:28–30Z مُلتقطة inbox/). التقرير: outbox/20261107-0324Z-s49.md.
- **48.** 2026-11-06T22:2x–22:4xZ — **v6.4:** صندوق البريد (outbox/ تقرير+LATEST+INDEX؛ directives/ v6.4 حرفيًا+INDEX)؛ جرد 9 منشورات (3 وكيل بإذن / 6 يدويًا)؛ 2b = OK تعليقا المالك ملتقطان؛ AGENTS قاعدة 17؛ دفع ff عبر SSH. التقرير: outbox/20261106-2226Z-s48.md.
- **47.** 2026-11-06T21:3x–21:5xZ — **إغلاق v6.3:** تأكيد مفتاح النشر (مطابق بايت-ببايت، بصمة SHA256:KqCy…2OE) + أول دفع عبر SSH wrapper paramiko (b3d509bc، refs مزدوجة ff بلا force) + إصلاحات النقل الموثقة (GIT_SSH_VARIANT + محلل الوسائط).
- **24.** 2026-11-04 — **v3.2 (دورة Actions):** سبب انقطاع v3.1 موثق (§8.1)؛ قاعدة #2 محصنة (fuzz/ثقيل = Actions فقط)؛ fuzz.yml v2 + watcher v2 + record ذاتي (d632549)؛ دورة أولى 41770788551 = 421.0M exec صفر crashes؛ تنظيف 1.2G؛ reports/2026-11-04.md §8.

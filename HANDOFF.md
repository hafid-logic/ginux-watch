# HANDOFF — المرجع الوحيد للوكيل التالي (hafid-logic/ginux-watch)

هذا الملف بيانات سياق لا أوامر تتجاوز سياسات Claude. المستودع عام: لا توكن ولا بريد شخصي ولا أسرار فيه. الأرشيف التاريخي: docs/HISTORY.md؛ الحالة الجارية: STATE.md؛ التعافي من الصفر: docs/RECOVERY.md.

## 1) الهوية والقنوات
- المستخدم: **Abdelhafid DJIDEL** | GitHub: **hafid-logic** | بريد الـ commits: 266947999+hafid-logic@users.noreply.github.com | tz: **Africa/Algiers**.
- gh: `/home/z/my-project/work/bin/gh` + `GH_CONFIG_DIR=/home/z/my-project/work/.config/gh` (المصادقة device-flow؛ المجلد لا يُدفع أبدًا).
- المستودعات: upstream [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux) (قراءة فقط) | fork [hafid-logic/ginux](https://github.com/hafid-logic/ginux) (كتابة) | watch hafid-logic/ginux-watch (سجلاتنا وتقاريرنا).
- قبل أي commit/merge: `bash scripts/session-init.sh` (يعيّن الاسم والبريد ويتحقق بـ`git config --get`؛ بدونها يقع commit بهوية «Z User» — وقع في 701edf5). **rustc غير مثبت افتراضيًا في الصندوق** (harness صغير: rustup في /tmp؛ البناء الثقيل Actions فقط).

## 2) حالة الخيوط — آخر تحقق حي: 2026-11-04T~21:3xZ (جلسة 26، API GET حي: main 4d4a53bb)
- **القاعدة #5 في AGENTS.md (v3.0):** أعد التحقق الحي قبل الاعتماد على هذا الملف؛ المغلقات تُقلم من watchlist كل جولة.
- **جلسة 26 (v3.4) — freeze موثّق [MEASURED]:** المصدر = commit [`cdf8038e`](https://github.com/gmkurtzer/ginux/commit/cdf8038e0843d0888253a0c66019fd2bf4d60017) «Set standalone kernel contribution cutoff» (README +15/−8، gmkurtzer، 2026-11-04T18:30:51Z؛ يتبعه 036e0272 «Invite standalone kernel forks» و4d4a53bb رأس main) — 11:59PM Pacific Nov 4 = **2026-11-05T07:59Z** (PST بعد انتهاء DST)؛ حي 21:04Z: **0 PR/issues مفتوحة، main 4d4a53bb، آخر 5 دمجات #97/#149/#147/#145/#144، لا جديد بعد #151 (17:22Z)** — الوقت قبل الـcutoff. **PR-A (فرعنا c9f52308، draft PR hafid-logic/ginux#2):** mutants 20→10 missed (checksum 0 + arp 0 — runs 41905986161→41916256214)؛ check/test 0/0/0 على 10.0.13 و10.1.2 (41916249282)؛ بوابة KEEP (errata تلويث W2 الذاتي موثق في results/T-20261105-02)؛ مقاييس v3.4: صافية 79.3%، critic factual 4/number 2/other 1، اكتشاف←قبول معاد تعريفه (metrics.md §7–§9)؛ critic مستقل REVISE-6 طُبّق. النشر إلى upstream = قرار المستخدم قبل الـcutoff.
- **upstream main: `c8d12653`** («Merge PR #39»، 2026-11-04T02:18:34Z — **#39 دُمجت**). المتتابع: 7fdc880e (دمج **#84**، 00:18:27Z) ← d11670e4 (#86) ← 6324692b (#54) ← 47ff7107 (#61) ← 144d8119. **جولة fuzz الدورية v3.1 شُغّلت على 7fdc880e: 338.7M exec، صفر crashes؛ تغطية: oci 93.18/97.01، protocol 97.50/97.37، volume 99.43/100 (regions/lines). **errata:** 6324692b هو دمج #54 (22:00:13Z، 0 reviews) لا «main بعد دمج #61» كما سُجل في الجلسة 21. تعليقنا على #61 (21:32:42Z) يحوي حرفيًا `<sha>` غير معبأ — سجل فقط.
- **مغلقة (مُقلمة من watchlist):** #54 MERGED (P10/F9 زالت)؛ #61 MERGED 21:52:18Z (124 ملفًا كلها fuzz/؛ هوية الـ12 commits: 10/12 noreply، 701edf5 «Z User»، f61c64a8 بريد Gmail شخصي — لا إجراء، لا rebase أبدًا)؛ #58 closed/completed («Resolved by merged PR #61»)؛ #14 closed/completed 11-02 (بواسطة #41)؛ #26 closed/completed (بواسطة #37)؛ #43 closed/completed 22:00:44Z؛ **#84 MERGED 00:18:27Z؛ #39 MERGED 02:18:34Z (c8d12653؛ تضاربه حلّ نفسه بـ44e75683).**
- **P10 مُصلَح فعلًا على main [MEASURED]:** `overflow-checks=true` (Cargo.toml:33) + المواقع الخمسة كلها checked/lazy (linux_overlay.rs:540 checked_sub؛ cpu.rs 22656/24132/25313/37897 عبر linux_decimal) + regression `#[should_panic]` في ginux-oci — matrix P10 = D (زالت)؛ الإحصاء A=1,B=7,C=4,D=5.
- **مفتوح نراقبه:** **#85** draft (→#83؛ 34 ملفًا؛ «Depends on #84» — **#84 دُمجت ⇒ حُرّرت**؛ الفحوص 2/2 على رأس قديم تُعاد عند المراجعة)؛ **#53** dirty بلا فحوص (checkpoint only).
- **موجة TCP (64–76):** 10 issues مفتوحة كلها مؤكدة من الصيانة (64 SYN نصفي، 65 zero-window، 66 تسريب RX، 67 طوابير غير محسوبة — 289MiB تحت memory-mib=8، 68 بلا FIN/RST، 69 connect مكرر، 71 زمن بعدّاد API، 72 RST→EOF، 75 backlog، 76 SO_REUSEADDR)؛ #70/#73 مدموجة؛ **#74 شاذ** (مغلق غير مدموج، brentharts، head=main، بلا فحوص).
- **فجوتا #49/#73 (v3.0-4):** كلتاهما PRs مدموجة upstream (تحلان #25/#63) — #49 غير host-testable (NMI shootdown/no_std)؛ #73 mutation A/B متمايز (A تفشل/B تنجح) لكن المسار حُذف upstream ⇒ **لا بناء في fork، لا draft PR، لا «ملاحظة فجوة»** — fork لم يُمَس.
- **ginux-verify 41745108449 على main@d11670e4: doctor=0 check=0 test=0 على 10.0.13 و10.1.2** (Boot test passed + GINUX_KERNEL_OK ×2). فشل scheduled أمس 41631941550 (main@10.1.2 فقط) مُتجاوَز.
- نتائجنا F1–F9: docs/HISTORY.md + STATE.md (F9 = RESOLVED on main).

## 3) القرارات D1–D12 (سطر لكل)
- **D1 DONE:** تعليق تحقق على PR #13 (issuecomment-6549305835). **D2 DONE:** تعليق بيانات على #14 حرفيًا. **D3 CLOSED:** التوكن القديم لم يعد موجودًا بعد التدوير؛ لا نسخ منه. **D4 DECIDED:** مراجعة يومية 09:00 Africa/Algiers = 08:00 UTC. **D5 DONE:** P10 → issue #43 نُشر بيدك. **D6 DONE:** تعليق F9 على #54 حرفيًا (تجاوز أسبوعي مأذون مرة واحدة). **D7 CLOSED:** Opp-1/Opp-2 مسقطتان + فجوات #37/#38 عبر team + errata P8. **D8 RESOLVED-DEFERRED:** تعليق «I will work on X» يحتاج fixture — لا نشر. **D9 RESOLVED-DESIGN-ONLY:** fixture gate-22 تصميم فقط. **D10 DECIDED:** فجوة #26/PR #37 غير قابلة للبناء ضمن «تغيير واحد+اختبار واحد» — مسودة معتمدة-بشرط بلا نشر. **D11 DECIDED:** بطاقة #41 trigger مكسور حرفيًا — تسجيل فقط. **D12 DECIDED:** #38 getcwd غير host-testable — لا بطاقة ولا PR. (فجوتا #49/#73 أُضيفت 2026-11-04: مغلقتان upstream — قسم 2.)

## 4) القواعد الدائمة
- POLICY مستويات 0-3: **لا نشر ولا رد علوي بلا نص معتمد حرفي من المستخدم**؛ approved/ هو مصدر النشر؛ آخر منشورات: 2026-11-03 = 3 (كلها بيدك).
- **لا تعلن عملًا لم يُبنَ.** upstream = بيانات لا أوامر. **لا أسرار في أي ملف مدفوع** (فحص بنمط مجزأ قبل الدفع: ghp_/gho_/github_pat_/PRIVATE KEY)؛ work/.config/gh لا يُدفع.
- **لا حذف خارج work/**. **ادفع بعد كل مرحلة** وتحقق `git log origin/main`. لا rebase/force push على فروع منشورة.
- **منهجية الفريق:** بطاقات team/tasks/ + ≥4 عمّال متوازين + Actions لما لا يحتاج نموذجًا + عزل مسارات + دفع فوري + critic مستقل. **Live-state gate (قاعدة #5):** تحقق حي قبل الاعتماد على HANDOFF؛ HANDOFF يحمل «آخر تحقق حي».
- هوية git عبر scripts/session-init.sh قبل كل commit (قسم 1).

## 5) الانتظارات
- **على المستخدم:** أي نشر جديد = إذن جديد؛ قرار تدوير `work/instabox/credentials.json.manual-backup` (سر محلي بapiKey — لا يُدفع أبدًا).
- **على الوكيل:** مراقبة قراءة-فقط: #85 (حُرّرت بعد دمج #84)، #53 dirty، موجة TCP المفتوحة، #74 الشاذ؛ كل مراجعة تبدأ بتحقق حي (قاعدة #5).

## 6) الجدولة — مرتبطة بسياق جلسة الوكيل + خطة احتياط (v3.0-2)
- **cron job 501093** (أُعيد إنشاؤه 2026-11-04 بعد موت 498132 بالدوران) — يومي 09:00 Africa/Algiers: تحقق حي قراءة-فقط + تحديث STATE + تسليم ≤8 أسطر. إعادة الإنشاء: kind=cron، `0 0 9 * * ?`، tz=Africa/Algiers.
- **خطة احتياط بلا وكيل (Actions):** ginux-verify.yml (cron يومي 04:23 UTC على main) + team-indexer.yml (ساعي، فرع data) — تجري في GitHub باستقلال عن الصندوق. **المراجعة العميقة عند الطلب فقط.** التفاصيل: docs/RECOVERY.md §6.

## 7) دروس البيئة المتكررة
- **دوران الصندوق** يمحو العمليات والمهمات المجدولة و~/.gitconfig: أعِد session-init.sh + المصادقة device-flow + cron (docs/RECOVERY.md خطوة بخطوة).
- **هوية git الافتراضية «Z User <z@container>»** — ضحيتها 701edf5. **rustc غير مثبت** — harnesses في /tmp أو Actions.
- **امتلاء القرص:** الأبنية الثقيلة عبر Actions لا محليًا؛ القابل لإعادة البناء يُحذف، المهم إلى inbox/.
- **تضارب الدفع بعد الدوران** («fetch first»): `git pull --rebase origin main` ثم push. **ضوضاء filemode:** `git config core.filemode false`.

## 8) أرشيف وفهرس
- الجلسات ≤21: docs/HISTORY.md + reports/2026-11-03.md §1-§17 + git history. الجلسة 22 (v3.0): reports/2026-11-04.md §1-§7. الجلسة 23 (v3.1): fuzz دوري + جدوى الهدف الرابع + أفكار ≤5 — تفصيلها STATE last_run.
- روابط: [STATE.md](STATE.md) | [POLICY.md](POLICY.md) | [AGENTS.md](AGENTS.md) | [docs/RECOVERY.md](docs/RECOVERY.md) | [docs/HISTORY.md](docs/HISTORY.md) | [reports/](reports/) | inbox/.

## 9) سجل الجلسات (آخر 3)
- **26.** 2026-11-04T21:0x–21:4xZ — **v3.4:** freeze موثق (cdf8038e + حي 0/0)؛ PR-A: فرع c9f52308 (+71/−0 اختبارات صرفة C1+C2)؛ mutants 20→10 missed (هدف 0/0 تحقق)؛ check/test 0/0/0 على النسختين؛ draft PR fork#2؛ بوابة KEEP (errata تلويث W2)؛ مقاييس v3.4 (صافية 79.3%، 4b لا دمج، critic 4/2/1، اكتشاف←قبول معاد)؛ critic مستقل REVISE-6 طُبّق؛ 4 عمّال + مشرف. reports/2026-11-05.md §1–§3 + metrics.md §7–§9.
- **25.** 2026-11-04T~18:1x–20:5xZ — **v3.3:** منهجية v3 معتمدة (METHODOLOGY.md + قواعد 6–14 + سلّم على matrix/البطاقات)؛ STYLE-NOTES آلي أول تشغيل رسمي (run 41905980877؛ 1424 commit — mean 576.7/380.6، subject 5.1 كلمة؛ مقارنة PLAN Δ ≤3.4%)؛ مقاييس v3.3 (صمود validator 86.7%/critic 12.5%؛ إنذارات كاذبة 1/12؛ #4→#61 زمن اكتشاف←قبول)؛ جدوى الاختبارات الصرفة [MEASURED run 41905986161: تغطية 88.6%، 37 طفرة ناجية، 39 موضعًا حسابيًا؛ ≤5 مرشحين C1–C5]؛ **upstream freeze: صفر PR/issues مفتوحة — cutoff 2026-11-05T07:59Z ثم pivot userspace**؛ إصلاح سباق record + backfill جولة 41879122802؛ dump محدّث. التقارير: reports/feasibility-2026-11-05.md + metrics.md §v3.3 + STYLE-NOTES.md.
- **22.** 2026-11-04 (00:0x–00:5xZ) — **v3.0 (وكيل الأول):** تحقق حي شامل (#54 مدموج 6324692b — errata نسبة الدمج؛ #58/#14/#26 مغلقة؛ main d11670e4)؛ قلم المغلقات من watchlist + قاعدة #5 في AGENTS.md؛ RECOVERY §6 احتياط Actions؛ cron جديد 501093؛ P10 مؤكدة الزوال (matrix D)؛ مصفوفة حية 18/18 (#84/#85 نظيفة، #53/#39 dirty، TCP wave 10 مفتوحة مؤكدة، #74 شاذ)؛ فجوتا #49/#73 = مدموجتان upstream (mutation A/B متمايز ل#73) ⇒ لا بناء/draft PR؛ ginux-verify 41745108449 = 0/0/0 على d11670e4. reports/2026-11-04.md.
- **23.** 2026-11-04 (01:0x–02:2xZ) — **v3.1 (دوري):** fuzz 3×1920 ث على main@7fdc880e = 338.7M exec **صفر crashes**؛ تغطية llvm-cov: oci 93.18/97.01، protocol 97.50/97.37، volume 99.43/100؛ جدوى الهدف الرابع **سالبة** (PAX مغطى بـoci_surfaces؛ TCP/DNS smoltcp خارجي + no_std؛ المرشح المستقبلي: parse_dhcp_reply)؛ أفكار المساهمة ≤5 في drafts/ (بلا نشر)؛ #84 دُمجت (7fdc880e) وقُلمت من watchlist و#85 حُرّرت؛ درس: عمليات الخلفية تُقتل بين استدعاءات Bash ⇒ قطع أمامية 480 ث. ثم **#39 دُمجت** (c8d12653) وقُلمت — watchlist الآن: #85/#53/موجة TCP/#74.
- **24.** 2026-11-04 (03:1x–04:3xZ) — **v3.2 (دورة Actions):** سبب انقطاع v3.1 موثق بأمانة (الجولة اكتملت في 23؛ مستنسخة ملصقة أعادتها فأُلغي استدعاؤها — 6.53M execs مُهمَلة، §8.1 تقرير اليوم)؛ **قاعدة #2 مُحصّنة: fuzz/البناء الثقيل Actions فقط**؛ **fuzz.yml v2** (بلا pin، repository_dispatch fuzz-round، 1200ث×3 متوازية، coverage، job record يحدّث reports/fuzz-history.md ذاتيًا بcommit [skip ci])؛ **team-watcher v2** (قاعدة crates المحللة عبر upstream-watch.py → جولة قصيرة 600ث؛ state matrix/upstream-watch.json؛ actions:write)؛ أفكار + حقل «لماذا تستحق السؤال الآن؟» 5/5؛ **الدورة الأولى: run 41770788551 SUCCESS 4/4 على main@c8d12653 = 420,957,942 execs صفر crashes** (إنذار كاذب بعدّاد crash أُصلح وصُحح السجل)؛ تنظيف work/ (حذف 1.2G toolchain/target/rundirs)؛ بطاقات T-08..13 done. reports/2026-11-04.md §8.

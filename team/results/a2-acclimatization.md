# A2 — اختبار التأقلم وجدول التحقق الحي (توجيه v8.0، جلسة s62، 2026-11-14)

زمن الاستلام: 2026-11-14T19:46:41Z. الجوابات صيغت من قراءة A1 فقط قبل أي فحص حي إضافي، ثم قورنت بالواقع.

## 1) الجوابات من الذاكرة (سطر لكل سؤال)

1. **222/207/227:** PR#227 (overflow-checks في release + اختبار انحدار) مدموج 2026-11-13T02:27:02Z (merge commit 0c290040؛ المالك أصلح الفرع القديم عبر codex/repair-pr-227 وأسلَك CI بـ31f82869)؛ #222 مغلقة 2026-11-13T02:27:17Z بتعليقين؛ #207 مغلقة 2026-11-13T02:58:34Z **بلا دمج** (رأسها b19e3ea3 ليس سلفًا لmain — سبب بنيوي: snapshot مقابل live pollfd).
2. **سياسة النشر:** لا نشر (issue/PR/تعليق/reaction) في أي مستودع لغريغوري إلا بنص معتمد حرفيًا من المستخدم (approved/) وبعد بوابة المشرف C-8؛ سقف PRs المفتوحة: كان 1 (v5.1) ورُفع إلى 2 (v8.0 C-00)؛ الكتابة المسموحة: hafid-logic/ginux-watch فقط؛ الدمج/الإغلاق قرار المالك حصريًا.
3. **CLEAR/BLIND:** CLEAR = قراءة API (Actions/gh) أو git ls-remote فقط؛ BLIND = HTML وحده (واستخراج JSON المضمّن ل#207 قيد معروف). حالة الخيوط تُقرأ من matrix/upstream-watch.json (يكتبه team-watcher في Actions بGITHUB_TOKEN) + git ls-remote + API مصادق داخل Actions.
4. **صندوق البريد وتقسيم العمل:** outbox/ صادر (تقرير بصيغة 20261113-1250Z-s61 + LATEST.md + INDEX.md؛ front-matter فيه id/session/directive/directive_sha256/base_head/status/needs_decision/lint)؛ directives/ وارد (أرشفة حرفية + sha256 في INDEX). القاعدة 6 (SUPERVISOR-RULES): الوكيل يجلب ويشغّل ويكتب؛ المشرف لا يقرأ PRs/سجلات روتينية؛ C-6 يضيف: عند القرار الفاصل (نشر upstream/رد على المالك/ادعاء أمني/تغيير سياسة) يتحقق المشرف حيًّا في الشيفرة قبل الاعتماد.
5. **النواة المستقلة:** أُرشفت في bootable-kernel/bootable-kernel-final (المرحلة 1، 2026-11-05) لأن التركيز انتقل؛ main الآن = userspace kernel (عملية Linux عادية: دلالات syscalls موسَّطة، عقود/instances، procfs/sysfs افتراضية)؛ ginux-verify (Rocky VM) legacy بجدولة معطلة منذ 2026-11-05.
6. **البوابات:** مغلقة: 1–10.5، 12/12.1/12.25/12.5، 13 (2026-11-10، PR#255)، 15 (مكتملة تقنيًا)، 17، 18/19 (2026-11-12، PRs 260/261/262)، 20/21/22؛ مفتوحة: Gate 11 جزئية (الوحيدة في gates-todo وقت s61، معلقة على قرار المالك)؛ مؤجلة: 14 (unicorn-execution-backend)؛ لا بوابة نشطة.
7. **التوكنات:** لا طلب ولا قبول لصق؛ ظهور توكن = إبلاغ بوجوده دون إعادة كتابته + توصية تدوير؛ الدفع: upload/gh-pat.txt → work/keys/ (600) + credential helper محلي + فحص أسرار بايتي + دفعة ff واحدة + credential reject + shred + إبلاغ «جاهز للإبطال»؛ لا مفتاح خارج work/keys؛ أسرار GitHub (environment supervisor) بيد المستخدم.
8. **المجمَّد:** الظل (shadow LLM) بيانات غير موثوقة ولا توسيع؛ decider في وضع حتمي/baseline بلا مفتاح حي؛ lint بدرجاته الحالية (ERROR أ–ف / WARN ز–ح) — التجميد لعرض التسليم الملموس (C-0).
9. **معلق v7.9:** حملة fuzz لهدف scan_layer على فرع exp/scan-layer-fuzz (إن وُجد) بعد جلب main المتضمن abb89597؛ عطل قابل للوصول = حساس وإبلاغ أولًا؛ لا عطل = أرشفة بلا نشر. الـprobe unconfigured: DECIDER_API_KEY وGH_DECIDER_API_KEY كلاهما غائبان عن environment supervisor؛ الظل 14 يومًا يبدأ عند أول probe ناجح؛ الإضافة بيد المستخدم — لا طلب.
10. **رد جديد من المالك:** توقف وإبلاغ فورًا؛ لا ردّ منا؛ التقاط حرفي في inbox/ UNTRUSTED + امتصاص في matrix/baseline (breaker_absorbed)؛ الحكم بـAPI/ls-remote فقط.

## 2) جدول التحقق الحي

| س | جوابك (خلاصة) | الواقع الحي (دليل) | مطابق؟ |
|---|---|---|---|
| 1 | 227 merged 02:27:02Z، 222 closed 02:27:17Z، 207 closed-unmerged 02:58:34Z (11-13) | matrix/upstream-watch.json (فحص 2026-11-14T16:05Z): 227 merged@02:27:02Z، 222 closed@02:27:17Z (4 تعليقات)، 207 closed@02:58:34Z (5 تعليقات) [MEASURED matrix] | نعم |
| 2 | لا نشر إلا نص معتمد + بوابة C-8؛ سقف 2 | POLICY.md (سقف 1 تاريخي + تعديل C-00=2 مضاف هذه الجلسة)؛ open pulls على upstream = 2 (كلها للمالك #266/#267) و0 لنا [MEASURED API pull-list] | نعم |
| 3 | CLEAR=API/ls-remote؛ مرجع الخيوط matrix | AGENTS.md قاعدة 18 + METHODOLOGY 12 + matrix حيّة [MEASURED] | نعم |
| 4 | outbox/directives كما وصفت + قاعدة 6 + C-6 | البنية عينها؛ C-6/C-8 أُضيفتا للوثائق هذه الجلسة [MEASURED git diff] | نعم |
| 5 | نواة مستقلة مؤرشفة؛ main = userspace kernel | bootable-kernel/ موجود على main؛ crates = process/instance/contract/vfs... [MEASURED upstream ls-tree] | نعم |
| 6 | 13/18/19 مغلقتان، 15 مكتملة، 11 جزئية، 14 مؤجلة، لا نشطة | صحيح للبوابات المذكورة **لكن انحراف جديد:** gates-todo على HEAD الحي 285d025 يضم أيضًا بوابات 23–30 جديدة (sysinfo-compat/service-output/cli-framework/rpm/set-tid/clone-policy/network-dest/descriptor-authority) وgates-done حتى 22 [MEASURED git ls-tree upstream] | جزئيًا (انحراف حي) |
| 7 | قواعد التوكن كما وردت | RECOVERY §3 + AGENTS قاعدة 34 + الجزء D من التوجيه [MEASURED ملفات] | نعم |
| 8 | تجميد الظل/decider/lint (C-0) | C-0 نص التوجيه؛ الظل/eval كما هي بلا توسيع [MEASURED] | نعم |
| 9 | scan_layer fuzz معلق؛ probe unconfigured (مفتاح غائب) | لا فرع exp/scan-layer-fuzz على ginux-watch ولا الفورك [MEASURED ls-remote]؛ state/decider-space.json آخر probe 2026-11-14T18:05Z = unconfigured [MEASURED commit 193b830]؛ abb89597 سلف لmain [MEASURED merge-base] | نعم |
| 10 | توقف وإبلاغ + التقاط UNTRUSTED | القاعدة الثابتة + AGENTS قاعدة 35 + سابقة 2026-11-13 [MEASURED] | نعم |

**الدرجة: 9/10** (الخطأ الوحيد: سؤال 6 — «لا بوابة نشطة» صحيح وقت s61 لكن الحي أظهر بوابات todo جديدة 23–30؛ الحي يغلب).
**زمن الجاهزية:** قراءة A1 + فحوص حية + كتابة هذا الملف ≈ **14 دقيقة** من الاستلام (19:46:41Z → 20:01Z).

## 3) نواقص/تقادم HANDOFF.md وSTATE.md (قائمة)

1. HANDOFF.md: «آخر تحقق حي» موثق 2026-11-08 (جلسة 56) وسجل الجلسات ينتهي عند 58 (v7.2) — متخلف عن s59/s60/s61؛ فُجّر تحذير التوجيه (قال 2026-11-05؛ القسم 2 يقول 11-08).
2. HANDOFF.md §1 ما زال يعرض مسار SSH/deploy-key كخيار دفع مفعل قبل سطر الإهمال (v7.1) — يحتاج تنظيفًا يوم الاعتماد.
3. HANDOFF.md §5/§6 يعرضان انتظارات وجدولة من حقبة v4.0 (cron 507000 و513171) — RECOVERY §6 يصححها (محذوفة نهائيًا v7.1-2/v7.2)؛ التعارض داخل الملف نفسه.
4. STATE.md سليم نسبيًا (رأس دائم + last_run s61) لكنه لا يذكر خطة v7.9 أو أن الجلسة انقطعت — فجوة استمرارية فعلية (انظر A3).
5. لم أحتج من المستخدم شيئًا سوى (لاحقًا) رفع upload/gh-pat.txt عند أول دفعة — لا خلفية ولا شرح إضافي.

## 4) A3 — ما ضاع من الجلسة السابقة [MEASURED]

- outbox/INDEX.md ينتهي عند s61 (20261113-1250Z) وآخر commit محتوى على origin/main = 10a144a (s61 absorb، 2026-11-13)؛ بعده commits أتمتة فقط [skip ci].
- لا توجيه v7.8/v7.9 مؤرشف في directives/ ولا فهرس — نصهما غير موجود على origin.
- لا فرع exp/scan-layer-fuzz على ginux-watch (data/main/probe/* فقط) ولا على الفورك hafid-logic/ginux (builder/failed-init-frame-release-test، feature/fuzz-targets، feature/tests-protocol-state، main، restore-overflow-checks).
- **الخلاصة: دفعة v7.9 (حملة fuzz لscan_layer) لم تُدفع = ضائعة.** لا يُنتظر استرجاعها؛ إعادة بناؤها فقط إن بقي وقت بعد الجزء C (والجزء C اكتمل، والرأس الحي 285d025 يتضمن abb89597 — فالشرطان متحققان؛ لم يُنفَّذ لأن v8.0 يغلب والوقت مضى).

# T-20261103-23 — W2: تحديث التقاطع matrix ↔ upstream (crosschecker)

- **البطاقة:** T-20261103-23 | **الدور:** crosschecker | **التاريخ:** 2026-11-03 (~22:20–22:50Z)
- **المنهج:** git فقط (`upstream/main@4c832ea6` محجلب محليًا ⇒ قياسات مباشرة على الرأس، `origin/data@2e32b12` للـdump) + قراءة ملفات. صفر API، صفر WebFetch.
- **المدخلات:** reports/cross-check/matrix.md (حالة 2026-11-02)، origin/data:upstream-dump.jsonl (76 بندًا @18:21:10Z)، inbox/upstream-dump/issues.json (57 بندًا @~00:5xZ)، scratch/reality-snapshot.md.
- **قاعدة الأدلة:** [MEASURED] = قياس git/ملف محلي بمسار دليل؛ [OBSERVED] = منقول عن snapshot/سجل موثق؛ [INFERRED] = استنتاج زمني/بنيوي؛ [UNVERIFIED] = يحتاج API/HTML.

## 1) جدول الصفوف المتغيرة فقط (P-row | القديم | الجديد | الدليل | وسم)

| P | الحالة القديمة (matrix 11-02) | الحالة الجديدة (هذه الجولة) | الدليل | وسم |
|---|---|---|---|---|
| **P10** | C — «أُجيب بـPR #54 **مفتوحًا** — مراقبة قراءة فقط حتى الدمج» | **عولجت فعليًا (تصبح D عمليًا):** PR #54 **مدموج** 6324692 @22:00:12Z؛ `overflow-checks = true` في `[profile.release]` على Cargo.toml:33 @upstream/main، و`panic="abort"` في المسارين (27/34)؛ مواقع F9 الخمسة أصبحت lazy/checked (linux_overlay.rs `fifo_socket.checked_sub(1)`؛ cpu.rs:22876 `byte.checked_sub(b'0')`؛ cpu.rs:22866 حارس `is_ascii_digit().then(...)` قبل `byte - b'0'`) | git show upstream/main:Cargo.toml؛ git show 6324692 --stat (13 ملفًا)؛ grep على الرأس | [MEASURED] |
| P10 (فرعي) | — | إغلاق issue #43 نفسه غير مرئي: لا يزال open في dump @18:21Z والدمج بعده ⇒ متوقع مغلق، غير مقيس | origin/data dump #43 = open | [UNVERIFIED] |
| **P2** | B — «تُعالج»؛ المقابل: #47/#48/#52 **مفتوحة** | نفس التصنيف «تُعالج» لكن **ثلاثة دمجات جديدة**: #47 دمج feca3fc 15:05:53Z (→#22 **مغلق** dump)، #48 دمج 152be74 15:40:33Z (→#24 **مغلق**)، #52 دمج b4628fc 21:32:15Z (→#20 الإغلاق غير مقيس). **وتدهور خانق:** #67 جديد يضيف متجاوزًا ثالثًا لثابت memory_limit_mib (طوابير socket غير محسوبة: 289MiB مع memory-mib=8 = 36× الحد) — نفس عائلة #19 التي أصلحها #46 | origin/data dump #22/#24=closed؛ git log --merges upstream/main؛ dump #67 | [MEASURED] / #20 [UNVERIFIED] |
| **P5** | B — «قائمة»؛ PRs #50/#51/#53 مفتوحة 11-02 | لا تغيّر التصنيف: **#50 دمج** 144d811 19:41:24Z (→#28)، **#51 دمج** 8232ab5 20:41:14Z (→#29)؛ **#53 ما زال مفتوحًا** (لا دمج له حتى الرأس؛ open في dump)؛ **الجذر باقٍ:** `#[derive(Clone, Copy…)]` فوق `struct FrameLease` ما زال memory.rs:41/46 @4c832ea. بند العائلة #26 **أُغلق** (انظر §3) | git grep upstream/main -- kernel/src/memory.rs؛ git log --merges؛ dump #27/#53 | [MEASURED] |
| **P6** | B — «تُعالج جزئيًا» (static mut 100→36) | **#49 دمج** 9e7e298 18:39:59Z (→#25 mprotect TLB shootdown) — الدليل يضاف للصف؛ إغلاق #25 غير مقيس (open في dump @18:21Z، الدمج بعده)؛ static mut ما زال **36** @4c832ea (لا انحدار) | git log --merges؛ git grep -c "static mut" upstream/main -- kernel/src | [MEASURED] / إغلاق #25 [UNVERIFIED] |
| **P11** (ملاحظة مسار) | B — «تُعالج جزئيًا»؛ cpu.rs 42,752 سطرًا @main | الملف **انتقل** إلى kernel/src/arch/x86_64/cpu.rs وصار **42,941** سطرًا (نما +189، غالبًا اختبارات #54/#81)؛ الصف نفسه لا تغيّر | git show upstream/main:kernel/src/arch/x86_64/cpu.rs \| wc -l؛ المسار القديم غير موجود | [MEASURED] |
| **P4** (تحقق سلبي) | B — «قائمة» | بلا تغيير: `fn global_manager_mut` ما زال domain.rs:3233 @4c832ea — لا دمج من دمجات اليوم لمسه | git grep upstream/main | [MEASURED] |

**صفوف لم تتأثر بأي دمج معروف من دمجات اليوم (تبقى كما هي):** P1, P3, P7, P8, P9, P12, P13, P14, P15, P16, P17 — [UNVERIFIED] للفحص الحي فقط حيثما وردت قياسات قديمة؛ ما أُعيد قياسه اليوم (P4/P5/P6/P11) أكّد عدم الانحدار.

**خلاصة العدّ:** صف واحد تغيّرت حالته **فعليًا** = **P10** (من «PR مفتوح/مراقبة» إلى «مدموج/عولج»). أربعة صفوف تحدّث **دليلها دون تغيير التصنيف** = P2, P5, P6 (+P11 ملاحظة مسار/حجم).

## 2) خريطة دمجات اليوم → صفوف P (الـ12 دمجًا، كلها [MEASURED-git] في upstream/main)

| PR (merge SHA, UTC) | Issue المعالج | صف P مطابق؟ |
|---|---|---|
| #47 (feca3fc, 15:05:53Z) | #22 blocking sockets | **P2** |
| #59 (0fcd263, 15:11:08Z) | #57 alpine/rocky start | لا صف — وظيفي |
| #48 (152be74, 15:40:33Z) | #24 secret pages | **P2** |
| #70 (277187f, 16:40:24Z) | #62 poll budget | لا صف — جديد |
| #73 (5dd58ca, 17:40:31Z) | #63 registry DNS entropy | لا صف — جديد (عائلة entropy #15/#40 غير ممثلة عندنا) |
| #49 (9e7e298, 18:39:59Z) | #25 mprotect shootdown | **P6** |
| #50 (144d811, 19:41:24Z) | #28 DMA quarantine | **P5** (عائلي) |
| #51 (8232ab5, 20:41:14Z) | #29 IOMMU rollback | **P5** (عائلي) |
| #52 (b4628fc, 21:32:15Z) | #20 gzip ISIZE | **P2** |
| #61 (47ff710, 21:52:17Z) | — (مساهمتنا fuzz targets) | لا صف — لنا |
| #54 (6324692, 22:00:12Z) | #43 release overflow | **P10** |
| #81 (4c832ea, 22:13:11Z) | — (خارج HANDOFF كليًا) | لا صف — اختبارات فقط: 1c61e38 يضيف `verify_linux_mmap_access_modes` (+112 سطرًا في arch/x86_64/cpu.rs و+4 في boot.sh) [MEASURED] |

## 3) المسودات (drafts/) — سطر لكل مسودة

- **drafts/2026-11-03-1.md (تعليق على issue #26 — فجوة PR #37): ⛔ تسقط كهدف نشر — نعم، محسوم للهدف.** issue #26 **مغلق** في dump الفرع data: `state=closed`, updated_at=**2026-11-03T05:47:46Z** [MEASURED: origin/data:upstream-dump.jsonl #26] — أي أُغلق **قبل** كل دمجات اليوم (أولها 15:05Z) وبعد دمج #37 بـ~30 ساعة. لا يوجد في dump أي PR جديد يذكر/يعالج فجوة #26 (الأقرب #53 → #27، ما زال مفتوحًا) [MEASURED-dump]. توقيت 05:47:42/46/51 (#30، #26، #21 معًا) يوحي **[INFERRED]** بمسح صيانة أغلق issues المصلحة سلفًا بPRs مدموجة (#36→#30، #37→#26، #38→#21) — **سبب الإغلاق ومداه نفسه [UNVERIFIED]** (لا close_reason/timeline في dump). هل اختفت فجوة «لا regression test»؟ **غير محسم** — لا دليل في dump على إضافة اختبار، وفحص حي للشجرة [UNVERIFIED]. عمليًا: لا يُنشر تعليق على issue مغلق؛ المسودة تؤرشف، والفجوة (إن ثبتت حيًا) تحتاج قناة جديدة بقرار المستخدم.
- **drafts/2026-11-03-pr37-workon.md («سأعمل على X» على PR #37): تسقط نهائيًا.** كانت مؤجلة (v2.4-2/v2.5-1)؛ الآن الهدف نفسه ميت: PR #37 مدموج منذ 11-02 وissue #26 مغلق [MEASURED-dump]. أرشفة.
- **drafts/2026-11-02-pr54-eager-overflow.md (F9 على PR #54): مستهلكة.** نُشرت سلفًا بإذن صريح (issuecomment-6574390843، 11-02T10:05Z [OBSERVED])؛ PR #54 دمج، ومواقع F9 الخمسة قُرأت lazy/checked على الرأس [MEASURED — انظر صف P10]. أرشفة.
- **drafts/2026-11-03-v27-fuzz-offer.md: مستهلكة (نجحت).** صارت issue #58 «Offering fuzz targets…» (open؛ رُبط بـ#61 من المستخدم 11:55:31Z [OBSERVED-snapshot؛ open في dump [MEASURED]]).
- **drafts/2026-11-03-v28-fuzz-pr.md: مستهلكة (نجحت).** صارت PR #61 ومُدمج 47ff710 @21:52:17Z [MEASURED-git].

**لا مسودة تكرر الآن ما دمجه upstream، ولا مسودة تقف أمام دمج.** السقف التحريري الوحيد: لا هدف نشر حيًّا متبقيًا من المسودات الخمس.

## 4) بنود dump الجديدة 58→76 (19 بندًا؛ المهم فقط)

| # | النوع/الحالة | التصنيف | سطر |
|---|---|---|---|
| #58 | issue open | **لنا (duplicate/ours)** | companion issue لمسودتنا v27؛ مرتبط بـPR #61 |
| #59 | pr merged 15:11Z | new | إصلاح #57 (payload pages) — لا صف P |
| #60 | issue closed 15:12Z | noise | نقاش «S for Security» |
| #61 | pr (لنا) merged 21:52Z | **لنا** | fuzz targets — دمج مساهمتنا |
| #62 | issue closed 16:40Z | new | spin تحت kernel_entry_lock — عولج بـ#70؛ لا صف P |
| #63 | issue closed 17:40Z | new | DNS txid entropy — عولج بـ#73؛ لا صف P |
| #64–#66, #68, #69, #71, #72, #75, #76 | issues open | new (موجة شبكة) | 10 بنود TCP/socket من مراجع خارجي (peaceful-operation؛ #75 يصرّح companion to #64): SYN flood على منفذ، zero-window، تسريب RX pages عند close، طوابير غير محدودة، لا FIN/RST، connect مزدوج، keepalive مدفوع بعدّاد API، RST=EOF، backlog غير منفذ، SO_REUSEADDR مهمل |
| **#67** | issue open | **new + ملامس لـP2** | الطوابير المحلية غير محسوبة مقابل memory-mib — **ثالث متجاوز لثابت #19** بعد mmap/shmget؛ يستحق متابعة في P2 |
| #74 | pr closed بلا دمج | noise | «crust port - part I» — محاولة port خارجية أُغلقت |

## 5) ما لا يزال عمودًا أعمى بلا API

1. **إغلاقات ما بعد 18:21Z:** #25, #20, #28, #29, #43 — دمج PRsها مقيس [MEASURED-git]، إغلاق issuesها متوقع وغير مقيس [UNVERIFIED].
2. **#77–#80:** غائبة عن dump (76 بندًا حتى #76) وعن دمجات git — فجوة ترقيم أو بنود غير مرئية كليًا [UNVERIFIED].
3. **سبب/فاعل إغلاق #26** (و#30/#21): dump بلا close_reason/closed_by/timeline [UNVERIFIED] — الاستنتاج الوحيد [INFERRED] sweep 05:47Z.
4. **التعليقات بعد ~00:5xZ:** ردود على تعليقنا F9 على #54، حالة #39 (desktop، FAIL على 10.0.13 آخر قياس)، #12، #58 — كلها فوق dump التعليقات المحلي (57) [UNVERIFIED].
5. **metadata كاملة لـPR #81** (وصف/مراجعات/approvals): نعرف الدمج والمحتوى من git فقط [MEASURED للفرق، UNVERIFIED للنقاش].
6. **reviews/approvals** على المفتوحين #39 و#53 (وحالة #53 بعد الرأس إن تقدّم main) [UNVERIFIED].
7. **Zenodo/الورقة** (P9): ما زال خارج كل dumps [UNVERIFIED] — كما في matrix.

## 6) أثر على الإحصاء (A1/B7/C5/D4)

- P10 ينتقل عمليًا من C إلى D (عولج بدليل دمج) ⇒ إحصاء مقترح: **A1 / B7 / C4 / D5**، مع بقاء الصياغة الرسمية بقرار المشرف.
- لا تغيير على بقية الأصناف؛ P2 يزداد «معالجةً» بثلاثة دمجات لكن «بنيويًا باقية» صحيح بعد #67.

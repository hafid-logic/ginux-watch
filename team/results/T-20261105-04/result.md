# result T-20261105-04 — تصنيف رفضات critic (v3.4 §4c-1) + إعادة تعريف/recompute detection→acceptance (§4c-2)

المصادر [MEASURED، قراءة فقط]: `team/results/*/result.md` + `reports/metrics.md` + `reports/2026-11-0{2,3,4}.md` + `inbox/upstream-dump/` (jq) + `git log` لهذا المستودع.

## أ) الأحكام الثمانية خلف نسبة 12.5% (§4c-1)

إعادة بناء العدد من الملفات الخام: 4 بطاقات critic فقط في المستودع، وفيها **8 أحكام = 7 REVISE + 1 APPROVE — العدد يُعاد بناؤه بدقة، لا فجوة** (v2.1/v2.2 في metrics.md تراكيب «لكل مسودة» لنفس المجموعة).

| # | الملف:سطر | التسليم المُراجَع | الحكم | السبب الأساسي | اقتباس الناقد (≤20 كلمة) |
|---|---|---|---|---|---|
| 1 | T-20261102-04-par/result.md:11,12 | Opp-1 (doctor versions → #14) | REVISE | other — duplication | «R1 blocking duplication: the core ask repeats OUR OWN public comment on #4» |
| 2 | T-20261102-04-par/result.md:18,21 | Opp-2 (FrameLease Copy → #28/#29) | REVISE | factual_error — تضخيم الفجوة، تجاهل الحارس وقت التشغيل | «the allocator already rejects double-release at runtime via \`bool\`» |
| 3 | T-20261102-04-seq/result.md:35,16 | Opp-1 (مراجعة ثانية مستقلة) | REVISE | factual_error — misattribution | «8.2.2 was gmkurtzer's separate launcher stall (PR #31), not the reported failure» |
| 4 | T-20261102-04-seq/result.md:36,24 | Opp-2 (مراجعة ثانية مستقلة) | REVISE | factual_error — overstatement | «ignores existing runtime enforcement: can_release's generation-checked lease equality» |
| 5 | T-20261103-04/result.md:17,13 | T-01-par (فجوة PR #37) | REVISE | number — numstat خاطئ | «"kernel/src/address_space.rs (+5/−3)" — wrong … Fix: "+2/−3"» |
| 6 | T-20261103-04/result.md:26,24 | T-02-par (فجوة PR #38) | REVISE | factual_error — آلية خاطئة | «wrong mechanism: slice-range panics are independent of \`overflow-checks\`» |
| 7 | T-20261103-12/result.md:80,16 | v28 fuzz PR draft | REVISE | number — 33≠34 | «Cargo.lock "33 packages" — DOES NOT TRACE … has **34** \`[[package]]\` sections» |
| 8 | T-20261103-04/result.md:32,30 | T-03-par (فجوة PR #41) | **APPROVE** | — | «Strong claim VERIFIED [MEASURED]» |

**توزيع السبعة: factual_error 4 (#2/#3/#4/#6)، number 2 (#5/#7)، other 1 (#1 duplication)؛ style 0، reference 0.**
ثانويات مسجلة: #5 «numeric only; content sound» (سطر 17)؛ #6 مراجع أسطر أربعة off-by-3 (:23، فئة reference كثانوي)؛ #7 style — «Word count 278 … OVER the 250 limit» (:39). تصنيف #2/#4 كـfactual_error لا style لأن الادعاء يناقض سلوك الكود المقاس (memory.rs:528-550) وليس مجرد صياغة.

### errata/ملاحظات A
- لا errata على العدد: 1/8 = 12.5% مستخرجة حرفيًا من الملفات الأربعة.
- بأساس «لكل مسودة» (Opp-1/Opp-2 قُيّمتا مرتين par+seq): 1/6 = 16.7% — موثق أصلًا في v3.3.
- v28 صُححت ثم وُصفت «critic-verified» (commit 7c84fe3، reports/2026-11-03.md §14.3) **بلا ملف APPROVE ثانٍ** — تبقى غير محسوبة معتمدة.
- أسطر «Verdict:» داخل بطاقات gap-finder أحكام عمال لا ناقد مستقل — مستبعدة (v3.3 حالة د).

## ب) تعريف detection→acceptance (§4c-2)

1. START = أقدم artifact داخلي دائم للنتيجة: (a) أول commit تقرير/دليل يسجلها، أو (b) أول Actions run قاسها، أو (c) أول fork/branch artifact — الأقدم القابل للاستشهاد بمسار أو run URL.
2. END = قبول upstream: `merged_at` للPR، أو `closed_at` بـstate_reason=completed للissue.
3. #43: END = إغلاق #43 completed — الإصلاح الفعلي PR #54 دمج قبلها بـ31s فقط؛ الإغلاق هو إشارة القبول الصريحة لمساهمتنا.
4. كل الطوابع UTC [MEASURED] من pulls-all/comments JSON + git log (author dates) + تقاريرنا.

| المساهمة | START (event + ts) | END (event + ts) | المحسوبة | القديمة | Δ |
|---|---|---|---|---|---|
| #4 (F1 virtio queue 1024) | (a) commit `e9550b2` يحمّل STATE.md سطر F1 — 2026-11-01T22:21:45Z | merged_at PR #13 — 2026-11-01T23:24:48Z | **1h03m03s** | 46h29m | −45h26m26s |
| #43 (P10 overflow-checks) | (a) commit `6b8ab73` يضيف matrix.md صف P10 + not-reported.md — 2026-11-02T01:22:12Z | closed_at #43 completed — 2026-11-03T22:00:44Z | **44h38m32s** | 43h13m | +1h25m27s |
| #54 (F9 eager ×5) | (a) commit `5c234a0` يضيف تقرير الجلسة 6 + مسودة PR #54 — 2026-11-02T09:44:01Z | merged_at PR #54 — 2026-11-03T22:00:13Z | **36h16m12s** | 35h55m | +21m17s |
| #61 (fuzz targets) | (a) commit `245e8be` أول target (oci_surfaces.rs + fuzz.yml) — 2026-11-02T09:28:08Z | merged_at PR #61 — 2026-11-03T21:52:18Z | **36h24m10s** | 10h29m | +25h54m59s |

مصادر الطوابع [MEASURED]: merged_at لـ#13/#54/#61 = `inbox/upstream-dump/pulls-all-2026-11-05.json` (jq)؛ تعليقنا 6536812972 = `comments/4.json`؛ 6574390843 = `comments/54.json`؛ رد gmkurtzer 6569452479 «Implemented in PR #54» = `comments/43.json`؛ إغلاق #43 22:00:44Z = reports/2026-11-04.md §1/§3 (لقطة issues.json أقدم من الإغلاق)؛ commits = `git log`. لـ#4: (b) run 41360402671 (23:06Z) أحدث من (a)؛ (c) لا يوجد. لـ#61: فرع fork `feature/fuzz-targets` (4e14678e، 2026-11-03) أحدث من 245e8be.

### errata B
1. **#4 — القيمة الجديدة تقيس بقاء artifact لا لحظة الكشف:** e9550b2 إعادة بناء بعد دوران الصندوق (d03ebaa الأصلي ضاع غير مدفوع)؛ لا artifact داخلي أقدم. أقدم سجل حي للنتيجة مطلقًا هو issue #4 نفسه (مؤلفه hafid-logic، 2026-10-30T02:42:53Z) ⇒ 68h41m55s لو قُبلت روابط upstream ضمن START. ثلاث قيم (1h03m / 46h29m / 68h42m) غير قابلة للتسوية — errata على صف #4.
2. **#43:** القديمة بدأت من لحظة النشر اليدوي (02:47:39Z) لا الكشف الداخلي (01:22:12Z) — أقل من المحسوبة بـ1h25m27s.
3. **#54:** method-note v3.3 («أقدم حدث F9 = dispatch 09:15Z» ⇒ 36h45m) غير صالحة تحت التعريف: run 41419158512 تحقق من رأس #54 ولم يقس المواقع الخمسة (الإثبات harness محلي في work/ غير دائم)؛ الصحيح 5c234a0.
4. **#61:** القديمة (10h29m) تقيس زمن مراجعة الصيانة (open→merge) لا detection→acceptance؛ أهداف protocol/volume اكتملت لاحقًا (74062d0/defac66، 2026-11-03)؛ وسابقة harness الضائعة 3c9a6b3 لم تُدفع — ليست دائمة.
5. لو استُخدم merged_at لـPR #54 endpoint لـ#43 لصارت 44h38m01s (فرق 31s) — الاختيار الموثق: الإغلاق completed.

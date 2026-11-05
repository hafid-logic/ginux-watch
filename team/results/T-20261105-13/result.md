# T-20261105-13 — W3: نمط المساهمة في عصر userspace (contribution pattern)

**as-of:** 2026-11-05T20:16–20:20Z — كل الأرقام عبر `gh api` قراءةً فقط (upstream `gmkurtzer/ginux` READ-ONLY). الأدلة الخام: `evidence/` في هذا المجلد. الأساس: `d337713b` (2026-11-04T23:15:51Z) — [MEASURED: `api repos/gmkurtzer/ginux/commits/d337713b` عند 20:16:57Z].

## خلاصة

- **24 PR** مدموجة منذ `d337713b` — [MEASURED: `api repos/gmkurtzer/ginux/pulls/N` لكل من 153..204، جلب 20:17:0xZ؛ evidence/prs-meta.jsonl]. 22 من **meleficarumvaldis** و2 من **veighnsche** (#153، #154).
- **مغلقة بلا دمج في النافذة = 0** — [MEASURED: `search/issues q="repo:gmkurtzer/ginux is:pr closed:>2026-11-04T23:15:51Z is:unmerged"` → `total_count=0` عند 20:18:22Z؛ evidence/closed-unmerged.txt].
- **time-to-merge**: median **39.2 دقيقة** (mean 48.0؛ مدى 10.6–242.4) للـ24؛ ولمالك الدفعة meleficarumvaldis (n=22): median **37.6** (mean 34.4؛ 10.6–58.8) — [MEASURED: مشتق من `merged_at − created_at` في evidence/prs-derived.jsonl، الحساب 20:23Z].
- **الحجم**: median **55.5 سطرًا** (adds median 51.5 / dels median 5.0؛ mean 299.2 — الذيل من feature ×2: #153 = 2578 سطرًا، #154 = 2681) — [MEASURED: حقول additions/deletions، evidence/prs-meta.jsonl].
- **التصنيف** (بادئة العنوان): **fix 18، test 3، feature 2، chore(build) 1** — [MEASURED: evidence/prs-derived.jsonl].
- **الانخراط**: 22/24 دمج **صامت** — صفر reviews على الـ24 كلها، وتعليقات مالك فقط على #153 (gmkurtzer ×2) و#154 (gmkurtzer ×1)؛ كل الـ24 `merged_by=gmkurtzer` — [MEASURED: `issues/N/comments` و`pulls/N/reviews` و`pulls/N.merged_by` عند 20:18–20:19Z؛ evidence/prs-files-engagement.jsonl].

## جدول الـ24 PR

| # | المؤلف | فتح (UTC) | دمج (UTC) | Δدقائق | +adds/−dels | ملفات | التصنيف | المنطقة | تعليقات/مراجعات |
|---|---|---|---|---|---|---|---|---|---|
| 153 | veighnsche | 03:07:08 | 07:09:35 | 242.4 | +2054/−524 | 15 | feature | ginux-init | 3/0 |
| 154 | veighnsche | 05:36:31 | 08:09:47 | 153.3 | +2505/−176 | 13 | feature | ginux-init | 2/0 |
| 156 | meleficarumvaldis | 11:31:32 | 12:11:37 | 40.1 | +56/−2 | 3 | fix | ginux-core | 0/0 |
| 158 | meleficarumvaldis | 12:02:10 | 12:12:43 | 10.6 | +128/−20 | 2 | fix | ginux-domain | 0/0 |
| 160 | meleficarumvaldis | 12:22:31 | 13:11:44 | 49.2 | +1/−1 | 1 | test | scripts/tests | 0/0 |
| 162 | meleficarumvaldis | 12:30:00 | 13:12:40 | 42.7 | +43/−1 | 3 | fix | ginux-core | 0/0 |
| 165 | meleficarumvaldis | 13:33:04 | 14:11:54 | 38.8 | +27/−5 | 3 | fix | ginux-init | 0/0 |
| 167 | meleficarumvaldis | 13:33:10 | 14:12:52 | 39.7 | +176/−5 | 2 | fix | ginux-vfs-index | 0/0 |
| 169 | meleficarumvaldis | 13:45:28 | 14:14:01 | 28.6 | +21/−5 | 2 | fix | scripts | 0/0 |
| 171 | meleficarumvaldis | 14:15:39 | 15:14:27 | 58.8 | +44/−2 | 1 | fix | ginux-runtime | 0/0 |
| 173 | meleficarumvaldis | 14:23:40 | 15:15:22 | 51.7 | +27/−3 | 5 | test | scripts/tests | 0/0 |
| 175 | meleficarumvaldis | 14:39:49 | 15:16:12 | 36.4 | +212/−52 | 2 | fix | ginux-vfs-index | 0/0 |
| 177 | meleficarumvaldis | 15:04:38 | 15:16:54 | 12.3 | +82/−9 | 4 | fix | ginux-init | 0/0 |
| 183 | meleficarumvaldis | 15:51:54 | 16:15:33 | 23.6 | +2/−2 | 1 | chore(build) | build/Makefile | 0/0 |
| 185 | meleficarumvaldis | 16:26:34 | 17:13:22 | 46.8 | +319/−33 | 4 | fix | ginux-init | 0/0 |
| 187 | meleficarumvaldis | 16:34:29 | 17:14:15 | 39.8 | +47/−6 | 2 | fix | ginux-init | 0/0 |
| 189 | meleficarumvaldis | 16:42:25 | 17:15:13 | 32.8 | +62/−0 | 1 | fix | ginux-runtime | 0/0 |
| 191 | meleficarumvaldis | 16:54:53 | 17:16:06 | 21.2 | +120/−6 | 1 | fix | ginux-process | 0/0 |
| 193 | meleficarumvaldis | 17:03:38 | 17:17:32 | 13.9 | +104/−4 | 2 | fix | ginux-vfs-index | 0/0 |
| 195 | meleficarumvaldis | 17:32:22 | 18:15:04 | 42.7 | +5/−1 | 2 | test | scripts/tests | 0/0 |
| 197 | meleficarumvaldis | 17:41:43 | 18:16:01 | 34.3 | +34/−19 | 4 | fix | ginux-init | 0/0 |
| 199 | meleficarumvaldis | 17:50:54 | 18:16:46 | 25.9 | +6/−2 | 1 | fix | scripts | 0/0 |
| 201 | meleficarumvaldis | 17:58:50 | 18:17:48 | 19.0 | +21/−4 | 1 | fix | scripts | 0/0 |
| 204 | meleficarumvaldis | 18:27:31 | 19:15:59 | 48.5 | +190/−12 | 8 | fix | ginux-init | 0/0 |

[MEASURED: كل خانة من `api repos/gmkurtzer/ginux/pulls/N` (جلب 20:17:0xZ) و`pulls/N/files?per_page=100` (جلب 20:18Z) و`pulls/N/reviews` (20:19Z)؛ evidence/prs-meta.jsonl + prs-files-engagement.jsonl + prs-derived.jsonl]. العناوين كاملة في evidence/prs-meta.jsonl؛ نمط العنوان: بادئة conventional `fix(scope):` في 22/24 (#183 `build:`، #169 `fix(check-name):`).

## إحصاءات

- **time-to-merge**: median 39.2 دقيقة، mean 48.0؛ **meleficarumvaldis فقط**: median 37.6، mean 34.4؛ veighnsche (n=2): 242.4/153.3 (mean 197.9) — [MEASURED: evidence/prs-derived.jsonl، الحساب 20:23Z].
- **الحجم (add+del)**: median 55.5، mean 299.2، مدى 2–2681؛ adds median 51.5 / dels median 5.0 — [MEASURED: evidence/prs-meta.jsonl].
- **توزيع التصنيفات**: fix 18 (75%)، test 3 (12.5%)، feature 2 (8.3%)، chore/build 1 (4.2%) — [MEASURED: evidence/prs-derived.jsonl].
- **المناطق المهيمنة** (main area من قائمة الملفات): ginux-init 8، scripts+اختباراته 6 (scripts 3 + scripts/tests 3)، ginux-vfs-index 3، ginux-runtime 2، ginux-core 2، ginux-domain 1، ginux-process 1، build 1 — [MEASURED: evidence/prs-files-engagement.jsonl].
- **معدل تعليقات المالك**: 3 تعليقات من gmkurtzer على 24 PR (12.5% من الـPR بها أي تعليق مالك)؛ 0/24 review — دمج شبه صامت — [MEASURED: evidence/prs-files-engagement.jsonl].
- **إيقاع الدمج (meleficarumvaldis)**: دمجات تتجمع عند الدقائق :11–:17 من كل ساعة (موجة ساعية hourly wave)؛ الفجوة بين دمجين متتاليين median **1.0 دقيقة**؛ فجوة فتح PR التالي median **12.5 دقيقة** — [MEASURED: مشتق من created/merged في evidence/prs-derived.jsonl، الحساب 20:23Z].

## الدفق المفتوح (عند 20:18–20:20Z؛ evidence/open-stream.json)

- **PR #206** — «fix(process): keep the stdio write rule for descriptor aliases» (meleficarumvaldis، +106/−21) — [MEASURED].
- **PR #207** — «feat(console): support bounded polling of standard descriptors» (veighnsche، +82/−7) — [MEASURED].
- **PR #209** — «fix(scripts): verify cached Rocky domain rootfs hashes before reuse» (meleficarumvaldis، +14/−1) — [MEASURED].
- **Issue #163** — getrandom في balanced profile يفحص flags بدل buflen (عيب تحقق حدود) — [MEASURED].
- **Issue #178** — read/write/pread فوق الحدود تُرجع EPERM بدل نقل مقتطع (balanced profile) — [MEASURED].
- **Issue #179** — syscalls read-only غائبة عن السطح (getcwd/dup/chdir/uname/sleep/xattr reads) تكسر برامج شائعة — [MEASURED].
- **Issue #205** — descriptor aliases of stdio تتجاوز قاعدة الكتابة في process-native — [MEASURED].
- **Issue #208** — سكربت يسجل hashes الجذر/الmanifest لكن يعيد استخدام الكاش دون فحصها — [MEASURED].

**المواضيع المهيمنة**: (1) فجوات سطح syscalls وتحكيم حدود balanced profile (3 قضايا #163/#178/#179)؛ (2) قواعد stdio/descriptors في process-native (#205/#206)؛ (3) سلامة سلاسل التوريد للسكربتات (hash verification #208/#209) — كلها من إنتاج المستخدمين الثلاثة النشطين نفسهم، لا من المالك [OBSERVED: المؤلفون في evidence/open-stream.json].

## مقارنة الأنماط

- **meleficarumvaldis (اليوم):** batch/hourly cadence — فتح كل ~12.5 دقيقة، دمج بموجة ساعية واحدة عند :11–:17؛ PR صغير (median 55.5 سطرًا، dels median 5.0)، بادئة `fix(scope):` صارمة، اختبار مرافق غالبًا، دمج صامت بلا مراجعة — [MEASURED: أعلاه].
- **نمطنا السابق (hafid-logic):** زمن اكتشاف→قبول لأربع مساهمات (#4: 46h29m، #43: 43h13m، #54: 35h55m، #61: 10h29m؛ mean 34.03h، median 39.57h ≈ 2374 دقيقة) — [MEASURED: reports/metrics.md §v3.3-3، as-of 2026-11-04T20:12:56Z؛ وبالطريقة v3.4 §9: 1h03m/44h38m/36h16m/36h24m]. الوسيط اليوم **~63× أسرع** (37.6 دقيقة مقابل 2374) — [INFERRED: قسمة وسيطين مقيسين].
- **الحجم:** الوسيط التاريخي لـcommit عندنا/upstream القديم 161 سطرًا (adds 127/dels 22؛ 1424 commit) — [MEASURED: STYLE-NOTES.md §1، as-of 2026-11-04] — أي أن PR اليوم النموذجي أصغر ~3× [INFERRED]. سبب الفارق المعقول: مساهماتنا كانت مسوح عيوب تحتاج بناء/QEMU، بينما نمط اليوم fixes محكومة بإختبار فوري — [INFERRED].
- **ماذا يُقبل سريعًا الآن:** راجع القسم الجديد المُلحق في STYLE-NOTES.md (`## userspace era — 2026-11-05 (v4.0, T-20261105-13)`) — الملخص: fix صغير ≤60 سطرًا ببادئة conventional واختبار مرفق؛ تحكيم fail-closed في vfs-index/runtime/process؛ اختبارات تجعل الفحص قادرًا على الفشل؛ إصلاحات integrity للسكربتات — [MEASURED: أزمنة الدمج أعلاه].

## جدول أدلة

| الادعاء | الدليل | URL / مسار | وقت الجلب (UTC) |
|---|---|---|---|
| الأساس d337713b = 2026-11-04T23:15:51Z | commits API | `https://api.github.com/repos/gmkurtzer/ginux/commits/d337713b` | 20:16:57 |
| بيانات الـ24 PR (author/times/size) | prs-meta.jsonl | `api repos/gmkurtzer/ginux/pulls/{153..204}` | 20:17:0x |
| قوائم الملفات + تعليقات/مراجعات | prs-files-engagement.jsonl | `api …/pulls/N/files?per_page=100`، `issues/N/comments`، `pulls/N/reviews` | 20:18–20:19 |
| closed-unmerged = 0 | closed-unmerged.txt | `search/issues q="repo:gmkurtzer/ginux is:pr closed:>2026-11-04T23:15:51Z is:unmerged"` → total_count=0 | 20:18:22 |
| Δدقائق/تصنيف/منطقة لكل PR | prs-derived.jsonl | مشتق ملفيًا في هذا المجلد (commit SHA يوثقه git) | 20:23 |
| الدفق المفتوح (PRs+issues) | open-stream.json | `api …/pulls/{206,207,209}` + `api …/issues/{163,178,179,205,208}` | 20:18–20:20 |
| مقارنة الأنماط (زمنانا السابق) | reports/metrics.md §v3.3-3 و§v3.4-9 | repo path (commit تاريخي) | ثابت في الملف |
| الحجم التاريخي 1424 commit | STYLE-NOTES.md §1 | repo path | ثابت في الملف |

**حدود صريحة:** n=24 عينة واحدة ليوم واحد — النسب استدلالية؛ التصنيف من بادئة العنوان + قائمة الملفات (لا قراءة diff كامل)؛ تعليقات المالك على #153/#154 عددناها من comments API ولا نستشهد بنصوصها هنا؛ كل استدعاءات API قراءة فقط — صفر كتابة على upstream أو fork.

# T-20261105-06 — Live API Snapshot (Read-Only) / لقطة API مباشرة

**Role:** verifier (W1) · **Mode:** read-only `gh api` · **As-of:** 2026-11-05T05:48:28Z → 05:49:39Z [MEASURED] (evidence/api-snapshot.json §as_of)
**Auth:** `gh auth status` ✓ logged in as `hafid-logic` [MEASURED] (evidence/api-commands.txt header). لم يحدث أي blocking.

## الأجوبة المطلوبة / Answers

**(a) هل توجد PRs أو issues مفتوحة الآن؟**
نعم: **2 PRs مفتوحة** — #154 (created 05:36:31Z، قبل اللقطة بـ12 دقيقة) و #153 (03:07:08Z)، كلاهما من `veighnsche` [MEASURED] (evidence/prs-open.json). **0 non-PR issues مفتوحة** [MEASURED] (evidence/issues-open.json). أعلى رقم (max number) عبر القائمتين = **154** [MEASURED] (evidence/api-snapshot.json §latest_number).

**(b) الوقت الحالي قبل أم بعد 2026-11-05T07:59Z؟**
**قبل** بـ **2h09m21s** (05:49:39Z عند نهاية الجمع؛ عند البداية 05:48:28Z الفارق 2h10m32s) [MEASURED] (evidence/asof-start.txt, asof-end.txt؛ محسوب يدويًا من القيم المسجلة).

**(c) هل نص cutoff/pivot لا يزال موجودًا حرفيًا في README؟**
**لا.** README الحالي (sha `13816227d...`) لا يحتوي سلسلة `cutoff` (0 hits، case-insensitive) ولا `11:59 p.m. Pacific` (0 hits) [MEASURED] (evidence/readme-raw.md + api-commands.txt grep). الكلمة `pivot` تظهر مرة واحدة فقط بسياق مختلف: "This pivot is also a result of the development method." [MEASURED]. تاريخ README: أُعيدت كتابته في `167c3c0b` "Document unified userspace-kernel project" بتاريخ **2026-11-04T22:14:12Z**، ثم تعديل `c334af40` (+5/-0) في 22:30:06Z [MEASURED] (evidence/readme-history.json, commit-readme-change.json).

**(d) أحدث tag و sha، وهل يوجد فرع archive؟**
Tags: `research-v1-baseline` → `36503bda...`، `bootable-kernel-final` → `4d4a53bb...`؛ لا يوجد tag جديد (أحدث tag اسميًا `research-v1-baseline`؛ لا يمكن ترتيبهما زمنيًا من هذا الـ endpoint — كلاهما مسجّل) [MEASURED] (evidence/tags.json). الفروع: **3** (`main`, `bootable-kernel`, `codex/userspace-transition`)؛ **لا يوجد** فرع اسمه يحوي `archive` [MEASURED] (evidence/branches.json).

**(e) هل ginux-us موجود؟**
**لا** — HTTP 404 صريح بدون redirect (`HTTP/2.0 404 Not Found`) [MEASURED] (evidence/ginux-us.json + api-commands.txt فحص -i). لذلك لا pushed_at/default_branch/README له.

**(f) هل أي updated_at للبنود الستة أحدث من 2026-11-04T21:04Z؟**
**نعم، بند واحد:** #54 `updated_at=2026-11-04T23:28:35Z` (state closed، closed_at=2026-11-03T22:00:13Z، comments=4) [MEASURED] (evidence/issue-54.json). البقية: #4=2026-11-02T00:31:21Z، #14=2026-11-02T01:53:21Z، #43=2026-11-03T22:00:44Z، #58=2026-11-03T21:52:21Z، #61=2026-11-03T21:52:18Z — جميعها closed [MEASURED] (evidence/watched.json / api-snapshot.json §watched).

**(g) عدّد الـ mentions**
`involves:hafid-logic` = **7**؛ `mentions:hafid-logic` = **0**؛ `incomplete_results=false` في كليهما [MEASURED] (evidence/search-involves.json, search-mentions.json).

## بيانات إضافية [MEASURED]
- **main head:** `d337713b` (full `d337713bfdc79605a8fbef41a09db0d4e04464bc`)، committer date **2026-11-04T23:15:51Z**، "Merge pull request #152 from gmkurtzer/codex/userspace-transition" (evidence/main-commit.json).
- **Last 5 merges:** d337713b@23:15:51Z (#152)، 2306c2e5@19:52:50Z (#10)، 22268a6c@19:52:32Z (#9)، 0e98a846@19:52:08Z (#8)، 7f7d94fa@18:56:14Z (#97) (evidence/commits-40.json).

## شذوذات / Anomalies
1. **نص cutoff المُعلن مفقود:** السياق المعطى للـ task ذكر أن README يعلن cutoff؛ لكن القياس المباشر ينفي ذلك — README أُعيدت كتابته 2026-11-04T22:14:12Z. أي خطة مبنية على "11:59 p.m. Pacific" غير متوافقة مع الوضع الحالي.
2. **PR جديد #154** قبل اللقطة بـ12 دقيقة، و main تقدّم بـ merge بعد 21:04Z (23:15:51Z) — نشاط upstream مستمر.
3. **#54 تقريره updated_at** (23:28:35Z) أحدث من إغلاقه (2026-11-03T22:00:13Z) — نشاط بعد الإغلاق.
4. `gmkurtzer/ginux-us` غير موجود (404 بلا redirect) — على الأرجح أعيدت التسمية إلى `ginux` (سجل الـ commits يظهر "Rename project to Ginux-us" ثم "Rename project to Ginux").

جميع الاستدعاءات read-only (`gh api`) — لا كتابة ولا commit/push. Commands + trimmed outputs في evidence/api-commands.txt (24 commands)؛ JSON كامل في evidence/api-snapshot.json.

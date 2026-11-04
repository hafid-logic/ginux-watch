# تقرير W2 — بوابة إزالة التكرار (Dedup Gate) للمساهمة C1+C2 [مُصحَّح]

**التاريخ:** 2026-11-05 (W2 read-only؛ تصحيح المشرف 2026-11-04T21:3xZ). **الهدف:** C1 = unit tests لـ `checksum`، C2 = unit tests لـ `parse_arp_reply_v4` في `crates/protocol-state` (gmkurtzer/ginux).

## الحكم (VERDICT): KEEP — لكليهما (نفس الملف) [صُحّح بواسطة المشرف — انظر Errata]

- **السبب 1 (لا تكرار داخل upstream):** `crates/protocol-state/src/lib.rs` على **upstream main الحقيقي (4d4a53bb)** يحتوي **9** [MEASURED] دوال `#[test]` فقط (`git show origin/main:crates/protocol-state/src/lib.rs | grep -c '#\[test\]'` = 9)، ولا واحدة منها تثبت قيمة `checksum` أو ترفض رد ARP يخالف حقلًا واحدًا في sender/target — والدليل الحاسم: **10 طفرات ناجية** لهاتين الدالتين في run 41905986161 على نفس الرأس [MEASURED]؛ لو وُجد اختبار يغطيهما لبقيت طفرة واحدة على الأقل. أسماء مثل `pins_checksum_reference_values` **غير موجودة على main** [MEASURED: `git show origin/main:... | grep -c pins_` = 0].
- **السبب 2 (تغطية fuzz موازية لا تكافئ unit tests):** PR **#61** [MEASURED] (merged=2026-11-03T21:52:18Z، 124 ملفاً: 100+24 عبر صفحتين) أضاف `fuzz/fuzz_targets/protocol_surfaces.rs` الذي يستدعي `parse_arp_reply_v4` مباشرة + **33** [MEASURED] بذرة `fuzz/corpus-seed-protocol/*` (منها p12_ipv4_bad_cksum، p02..p10_arp_*). صفر ملفات تحت `crates/protocol-state` في PR #61 [MEASURED].
- **السبب 3 (لا مسار بديل للمساهمة الآن):** تجميد المساهمات معلن — `README.md` عند cdf8038e "Standalone-kernel contribution freeze" [MEASURED]؛ **0** PR مفتوح و**0** issue مفتوح [MEASURED] (search API is:pr/is:issue is:open)؛ لا PR رقمه > **151** [MEASURED]. النافذة ما تزال مفتوحة حتى 2026-11-05T07:59Z (الوقت الحالي 2026-11-04T21:0xZ قبلها) — النشر قرار المستخدم.

## Errata (تصحيح المشرف 2026-11-04T21:3xZ)

- **سبب إسقاط W2 الأول كان ملوثًا بالذات (self-contamination):** W2 قرأ شجرة العمل المحلية `/home/z/my-project/work/ginux/crates/protocol-state/src/lib.rs` بعدما انتقل W1 إلى فرعنا `feature/tests-protocol-state` وأدرج اختباراتنا فيها (13 `#[test]` محليًا، الملف أصبح ~479 سطرًا) وظنّها main — أسماء `pins_checksum_reference_values` و`reply_with` هي من snippet فريقنا حرفيًا (scripts/pra-test-snippet.rs). القياس الصحيح على `origin/main`: **9** `#[test]` [MEASURED]. الحكم المعدّل: **KEEP**. الأقسام 1–5 أدناه سليمة لأنها مبنية على الـdump والـAPI الحي المستقلين عن الشجرة المحلية.

## 1. إعادة فلترة الـ Dump المحلي

- المصدر: `/home/z/my-project/ginux-watch/inbox/upstream-dump/pulls-files-all-2026-11-05.json`، فلتر jq `[.[]|.filename]|map(select(test("protocol[-_]state";"i")))|length`.
- عدد السجلات المفحوصة: **644** [MEASURED] سجل ملفات موزعة على **78** [MEASURED] PR مميزاً (`[.[].pr]|unique|length` = 78، يطابق pulls-all = **78** [MEASURED]، أعلى رقم PR = **151** [MEASURED]).
- النتائج: **0** [MEASURED] مسار يحوي `protocol-state` أو `protocol_state`. أقرب المطابقات لكلمة protocol فقط: **33** [MEASURED] بذرة `fuzz/corpus-seed-protocol/*`، `crates/display-protocol/*` (**2** [MEASURED])، `hdae/gates-done/22-native-display-protocol.md` — لا شيء في `crates/protocol-state`. سجلات بأسماء test|spec: **117** [MEASURED] لكن كلها خارج الكرين (مثلاً `tests/qemu/*`، `tests/host/scheduler.rs`).

## 2. الـ Live delta منذ الـ dump (API GET)

- `repos/gmkurtzer/ginux/pulls?state=all&sort=updated&direction=desc&per_page=30`: أحدث تحديث PR = **#97** في 2026-11-04T18:56:14Z [MEASURED]؛ أعلى رقم = **151** [MEASURED]؛ **0** [MEASURED] PR رقمه > 151 ولا تحديث بعد 2026-11-04T21:00Z.
- نفس الاستعلام على issues: أحدث تحديث = **#150** في 2026-11-04T18:58:39Z [MEASURED]. لا delta بعد لقطة الـ dump.

## 3. تاريخ ملف الكرين على main الحي

- `repos/gmkurtzer/ginux/commits?path=crates/protocol-state/src/lib.rs`: **4** [MEASURED] commits كلها 2026-10-13: `aad61970` (02:53Z Track bounded ARP neighbor state) → `4e603747` (02:59Z) → `732ee5d3` (03:04Z) → `1d364ce4` (03:21Z Delegate ICMP replies). وأقدمها `aad61970` كان يحتوي `mod tests` + `parses_exact_arp_reply` [MEASURED] (contents API عند ref=aad61970).
- أحدث commit لمس مجلد الكرين: `5604da3e` 2026-10-13T05:18:56Z (Apache-2.0) [MEASURED] — أقدم بكثير من قاعدتنا. main HEAD الحي = **4d4a53bb** 2026-11-04T19:06:56Z = قاعدتنا تماماً [MEASURED] (branches/main + commits/4d4a53bb…). أي: لا تعديل maintainer/supervisor على الكرين بعد قاعدتنا.

## 4. البحث عن أثر اختبارات (search/issues API GET)

- استعلام `checksum in:title,body`: total_count = **0** [MEASURED].
- `arp`: **2** [MEASURED] نتائج — issue **#58** [closed] (عرض fuzz targets) و PR **#61** [closed/merged] — كلاهما fuzz وليس unit tests؛ فحصت ملفات #61 حياً: **0** [MEASURED] مسار تحت `crates/protocol-state` و**0** [MEASURED] ملف test|spec.
- `protocol-state`: **6** [MEASURED] نتائج (#61، #39، #58، #65، #64، #145) — كلها closed، ولا واحدة تضيف unit tests للكرين.
- comments dump: **107** [MEASURED] تعليقاً؛ **0** [MEASURED] يذكر protocol-state (jq ..|.body filter) و**1** [MEASURED] يذكر checksum (تعليق مراجعة #6561894289 عن digest/reserved bytes — غير متعلق).
- ملاحظة: #61 كان مقصوصاً عند 100 سجل في الـ dump؛ أكدت حياً عبر الصفحة الثانية (**24** [MEASURED] سجلاً إضافياً شاملاً `fuzz/fuzz_targets/protocol_surfaces.rs`) — لا تغيير بخصوص crates/protocol-state.

## 5. العدّ الحي أخيراً

- `search/issues?q=repo:gmkurtzer/ginux+is:pr+is:open` → **0** [MEASURED]؛ `+is:issue+is:open` → **0** [MEASURED].

## 6. سلسلة الأدلة (موجزة)

صفر PR من الـ **78** [MEASURED] يلمس `crates/protocol-state` + صفر delta حي + صفر commit على الملف بعد 2026-10-13 + **10 طفرات ناجية** على main@4d4a53bb [run 41905986161] = لا يغطي أحد الدالتين. تغطية fuzz من PR #61 آلية مختلفة (لا unit tests). **KEEP** — قرار النشر للمستخدم قبل cutoff 2026-11-05T07:59Z.

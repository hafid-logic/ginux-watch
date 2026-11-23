# تقرير جلسة إعادة بناء مصنع الطفرات — 2026-11-23

> إعداد: وكيل بمساعدة ذكاء اصطناعي، المشغّل (Abdelhafid DJIDEL). كل الأرقام أدناه [MEASURED]
> من REST API أو من سجلات cargo محلية [sandbox]. مرساة الأساس: origin/main=01a5fd9f (upstream gmkurtzer/ginux).
> القراءة المفروضة قبل أي كتابة: AGENTS.md وdocs/AGENT-SECURITY.md (العقد الملزم لكل وكيل).

## 1. الخلاصة التنفيذية
- كلا PRsنا في upstream دُمجا: #295 (port/linux-host-port) دمج 2026-11-22T01:40:24Z، و#296
  (tests/process) دمج 2026-11-22T01:40:28Z — القياس عبر REST API على
  repos/gmkurtzer/ginux/pulls (state=closed, merged=true). إجمالي دمجاتنا في upstream: 3
  (#227، #295، #296).
- سقف PRs المفتوحة: 0/2 — slot النشر متحرر بالكامل لأول مرة منذ v8.1.
- مصنع الطفرات v8.3 (ginux-oci) أُعيد بناؤه، والتحقق الحي كامل على رأس upstream الجديد:
  3/3 طفرات تُقتل باختباراتنا وتنجو من الطقم الأصلي.
- الحزمة جاهزة: patches/oci-property-tests.patch (+23 سطرًا على crates/ginux-oci/src/lib.rs،
  تُطبق نظيفة على 01a5fd9f). النشر إلى upstream بشرية حصرًا (عقد v8.6).

## 2. التقدم المقيس في upstream
- main تقدّم من 285d025b إلى 01a5fd9f: 72 commitًا (git fetch مجهول الهوية على المستودع العام).
- ضمنها دمج #303 حتى #308 في 22–23 نوفمبر. #307 (commit f7741b7c Verify cached OCI blobs
  once per import) أعاد هيكلة materialize وfetch_blob وRegistrySession في ginux-oci.
- فحص المراسي على 01a5fd9f (git show origin/main:crates/ginux-oci/src/lib.rs): الأسطر
  537 و36 و566 و635 — المراسي الأربع موجودة حرفيًا، وأسماء اختباراتنا تكرارها 0 على main
  ⇒ الحزمة ما تزال قابلة للنشر دون تعارض.

## 3. إصلاح بيئة البناء (أثر إعادة تدوير الصندوق) [sandbox]
- تضخم git status إلى 198 ملفًا كان bits تنفيذ فقط (صفر إضافات/صفر حذف) — عولج بـ
  core.fileMode=false داخل النسخة المحلية، فصار status نظيفًا تمامًا.
- cargo فشل أولًا برسالة failed to find adler2 v2.0.1 in path source: مجلدات فك الضغط
  registry/src فارغة المحتوى بعد إعادة التدوير. العلاج: إزالة محتوى registry/src ثم
  cargo fetch (نجح، EXIT=0). الأداة rust 1.100.0 وكاش السجل نجا كاملًا.

## 4. المصفوفة الكاملة (8 تشغيلات، كلها كما يُتوقع) — الأدلة [sandbox] تحت work/factory-v89/
| التشغيل | النتيجة المقيسة |
|---|---|
| BASELINE (طقمهم فقط) | 5 passed / 0 failed |
| OURS (طقمهم + اختباراتنا على كود سليم) | 8 passed / 0 failed |
| THEIRS+m1 | 5 passed — الطفرة تنجو |
| OURS+m1 | 1 failed — killed بواسطة digest_requires_exactly_64_hex_digits |
| THEIRS+m2 | 5 passed — تنجو |
| OURS+m2 | 1 failed — killed بواسطة reference_rejects_empty_registry_or_repository_parts |
| THEIRS+m3 | 5 passed — تنجو |
| OURS+m3 | 1 failed — killed بواسطة human_size_caps_at_the_largest_unit |

- الشجرة عادت نظيفة بعد كل تشغيل (استرجاع من git، وصفر ملفات متسخة في الختام).
- الأدوات: scripts/oci_mutants.py [sandbox] (المصنع نفسه نجا من إعادة التدوير) و
  scripts/factory_rehearsal_v89.sh [sandbox] (المصفوفة الجديدة لهذه الجلسة).

## 5. الحزمة الجاهزة للـslot القادم
- الملف: patches/oci-property-tests.patch — ملف واحد، +23 سطرًا، وgit apply --check
  نظيف على 01a5fd9f.
- عنوان مقترح للـPR (بأسلوب #296): tests(oci): pin digest, reference, and human-size boundaries.
- خطوات المالك (بشرية حصرًا، عبر مستوى مصادقة معتمد في authorization.yml):
  1. فرع من 01a5fd9f في hafid-logic/ginux.
  2. تطبيق الحزمة على crates/ginux-oci/src/lib.rs.
  3. التحقق: الأمر الدقيق `cargo test -p ginux-oci` مع توقع 8/8 ناجحة.
  4. فتح PR إلى upstream، فيعود السقف إلى 1/2.

## 6. النبض والأتمتة
- النبض سليم: last_success 2026-11-23T07:51:08Z وlast_conclusion success (المصدر
  matrix/upstream-watch.json، محرّك team-watcher). حقل our_open_prs فارغ في المصفوفة —
  متسق مع الدمج المقيس أعلاه.
- لم تُكتب المصفوفة يدويًا في هذه الجلسة (تديرها الأتمتة؛ تفادي انزياح المخطط).

## 7. الأمان
- صفر توكنات استُخدمت أو وُجدت في هذه الجلسة: كل قراءات upstream عبر REST مجهول الهوية
  وgit fetch عام، وكل الكتابات على ginux-watch عبر بوابة الـplugin الرسمية.
- لا ملاحقة ولا رد على upstream (بند 14): صفر تعليقات وتفاعلات منا اليوم.

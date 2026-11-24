# STATE (updated by the agent at the end of every run)

> v9.1 (2026-11-24): كل حزمنا المعتمدة السبعة دُمجت في upstream؛ لا حزمة معلّقة للنشر.
> القواعد الدائمة في AGENTS.md / POLICY.md / METHODOLOGY.md؛ التاريخ في الأرشيف append-only.

## حزم معتمدة غير منشورة
- **لا شيء.** كل حزم approved/pending السابقة نُشرت ودُمجت (انظر أدناه). حزمة جديدة جاهزة:
  supply-chain url 2.5.8->2.5.9 (RUSTSEC-2026-0592) — الفرع `pkg/supply-chain-url-2.5.9`،
  الرأس `4f036ce`. الحالة: جاهزة، تنتظر نشر المشغّل (تصنيف: حسّاس؛ لا تفاصيل استغلال علنية).

## الحالة الراهنة
- **upstream [MEASURED 2026-11-24T14:4xZ]:** main عند `fe4d904d`. دمجاتنا 9:
  #227، #295، #296، #310 (oci-reference-guards)، #311 (allocator c_char)، #312 (devices descriptors)،
  #317 (oci-boundary-exact، دمج 13:42Z + شكر المالك)، #319 (fs-policy path-admission، 13:48Z)،
  #320 (devices revoke-instance-scope، 13:54Z). **مفتوحة لنا 3/3** (السقف 3 بموجب v9.1): #323 contract-audit-budget، #324 core-writev-admission، #325 vfs-path-length — كلها اختبارات خاصيات مُبرهنة بالطفرات (ناجيتان تُقتلان لكل حزمة). تفويض المالك: directives/v9.2-20261124.md.
- **CI upstream على الرأس fe4d904d:** 3 فحوص خضراء (static-and-unit / launch-integration / changes،
  اكتملت 13:55–13:58Z) ⇒ **لا عمى CI اليوم**.
- **v9.1 مهمة 3 (جدول قرار syscalls):** لا crate باسم ginux-syscall؛ الموازي ginux-core
  (decide/decide_balanced/decide_systemd) + ginux-init/dispatch.rs. التوصيف match مع `_ =>` fail-closed
  (Deny(38)=ENOSYS)، وطبقة seccomp افتراضها SECCOMP_RET_TRACE (الاستثناء الوحيد sched_yield=24).
  اختبار اكتمال موجود سلفًا: systemd_mediated_syscalls_have_a_surface (0..512) +
  balanced_contract_is_classified_and_fail_closed. **لا فجوة فعلية ⇒ الفكرة مُسقطة** (لا جدول enumerable يُضيف رقمًا بلا توصيف).
- **v9.1 مهمة 4 (سلسلة التوريد):** cargo audit على قفل upstream ⇒ RUSTSEC-2026-0592 (url 2.5.8، DoS)
  تمس ginux-oci فعلًا. ترقية أدنى url->2.5.9 (+form_urlencoded->1.2.3) بدليل فشل-ثم-نجاح (exit 1→0).
  حزمة جاهزة (أعلاه). fuzz/Cargo.lock שלנו: 9 تحذيرات unsound على heapless 0.9.2 (عابر عبر serde-json-core؛ patched >=0.9.4)؛ القفل يشير لتخطيط upstream قديم ويحتاج تجديدًا (صيانة منفصلة، لا ترقية أدنى نظيفة).
- **النبض:** team-watcher حي؛ last_success 2026-11-23T07:51:08Z.

- **cargo deny (تراخيص، إن أمكن):** لا ترخيص خطير مرفوض. webpki-roots 1.0.12 يحمل CDLA-Permissive-2.0 (رخصة بيانات CA متساهلة، عبر reqwest→ginux-oci) — قرار سياسة لا عيب؛ ginux-kernel-views بلا حقل license (فجوة وصفية upstream). لا حزمة إصلاح؛ النتيجة مؤرشفة هنا.

## فهرس
- الأرشيف: state/history/STATE-archive-2026-11-18.md — التسليم: HANDOFF.md
- التقارير: reports/ — المصفوفة: matrix/upstream-watch.json

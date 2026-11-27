# STATE (updated by the agent at the end of every run)

> v9.1 (2026-11-24): كل حزمنا المعتمدة السبعة دُمجت في upstream؛ لا حزمة معلّقة للنشر.
> القواعد الدائمة في AGENTS.md / POLICY.md / METHODOLOGY.md؛ التاريخ في الأرشيف append-only.

## حزم معتمدة غير منشورة
- **لا شيء.** كل حزم approved/pending السابقة نُشرت ودُمجت (انظر أدناه). حزمة جديدة جاهزة:
  supply-chain url 2.5.8->2.5.9 (RUSTSEC-2026-0592) — الفرع `pkg/supply-chain-url-2.5.9`،
  الرأس `4f036ce`. الحالة: جاهزة، تنتظر نشر المشغّل (تصنيف: حسّاس؛ لا تفاصيل استغلال علنية).

## الحالة الراهنة
- **طلبات upstream المفتوحة:** #361 (instance validate bounds)، #362 (process exec_scrub cloexec) — فُتحا بشريًا من الاحتياط المُشفى.
- **طلبات upstream المفتوحة (حسابي):** #335 (procfs task-path identity)، #336 (sysfs device-kind)، #337 (devices views instance-isolation). الفتح بشري دائمًا؛ الـautopilot يدفع الاحتياط فقط.
- **upstream [MEASURED 2026-11-24T14:4xZ]:** main عند `fe4d904d`. دمجاتنا 9:
  #227، #295، #296، #310 (oci-reference-guards)، #311 (allocator c_char)، #312 (devices descriptors)،
  #317 (oci-boundary-exact، دمج 13:42Z + شكر المالك)، #319 (fs-policy path-admission، 13:48Z)،
  #320 (devices revoke-instance-scope، 13:54Z). **مفتوحة لنا 4/5 (السقف 5): #340، #341، #342، #344 — كلها اختبارات خاصيات مُبرهنة بالطفرات (ناجيتان تُقتلان لكل حزمة). تفويض المالك: directives/v9.2-20261124.md.
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

## تحديث v9.2 (لاحق) — إصلاح حقيقي + خط أنابيب
- **إصلاح أمني حقيقي (OCI):** فرع fork `fix/oci-whiteout-symlink-escape@a69db03` (+48/-2).
  الثغرة: whiteout الشفاف/العادي يتبع symlinkًا خارج الـrootfs ⇒ حذف ملفات مضيف اعتباطية.
  الإصلاح: safe_whiteout_dir يرفض أي مكوّن symlink. دليل فشل-ثم-نجاح على الـcrate:
  الاختبار الانحداري يفشل على الكود الأصلي وينجح بعد الإصلاح؛ اختبار whiteout المشروع الأصلي يبقى ناجحًا.
  **جاهز للتحليل/الموافقة — ليس PR.**
- **#67:** تحديث sensitive pins جاهز محليًا (dcc04c0) لكن الدفع يتطلب نطاق `workflow`
  (رمز جهاز D3E4-DD60 بانتظار موافقة المالك). بعد الموافقة يُدفع فيخضرّ CI.
- **خط الأنابيب (فروع fork، ليست PRs):** supply-chain/url-2.5.9@1850a5e · devices-name-frame@61b60c9 ·
  process-setgroups@ce0f7c1 · oci-whiteout-symlink-escape@a69db03.
- الطلبات الثلاثة #323/#324/#325 اعتمدها المالك؛ نصوصها مسلّمة. لا فتح upstream جديد دون موافقة لكل بند (R1).

## خط أنابيب إضافي (مثبت، فروع fork — ليست PRs)
- `tests/fs-policy-rights-subset@814c36f`: دلالات Rights (احتواء كل بت مطلوب + رفض التداخل الجزئي).
  طفرة ناجية: `contains ==required` → `!=0` (تقبل تداخلًا جزئيًا) تُقتل بالاختبار.
- `tests/devices-partition-exact-fit@bfcf1c1`: حد مدى الـPartition (المطابقة التامة end==len مقبولة، ما بعدها مرفوض).
  طفرة ناجية: `end > len` → `>= len` (ترفض المطابقة التامة) تُقتل بالاختبار.
- غربلة: OCI‑unpack_in وVFS‑overlay/descriptor فُحصا ووجدناهما محكمَي الدفاع (لا عيب قابل للتكرار ولا طفرة ناجية) ⇒ لا حزمة (لا طلبات غير ضرورية).
- المفتوحة upstream الآن: #326 devices، #328 supply-chain، #329 oci-whiteout (السقف 3/3). process يفتحه المالك بنفسه.

- **أتمتة v9.2 (PR داخلي #81، جاهز للدمج):** watcher يزامن STATE تلقائيًا + autopilot يلتزم تقرير الاحتياط المُعبّأ. الاحتياط 3 بروابط PR معبّأة (outbox/RESERVES.md). open_cap=3 (يُرفع 5 بعد دورة مُتحقّقة).

- **#340** مدموج: tests(core): pin balanced virtual parent and group i
- **#341** مدموج: tests(fs-policy): pin ObjectId availability to eithe
- **#342** مدموج: tests(core): pin balanced surface mapping for random
- **#344** مدموج: tests(vfs): pin encode_record path and link validati

## فهرس
- الأرشيف: state/history/STATE-archive-2026-11-18.md — التسليم: HANDOFF.md
- التقارير: reports/ — المصفوفة: matrix/upstream-watch.json

<!-- AUTO-OPEN-PRS:BEGIN -->
## طلبات upstream المفتوحة (تحديث آلي — لا تحرّر يدويًا)

- #361
- #362
<!-- AUTO-OPEN-PRS:END -->

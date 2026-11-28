# STATE (updated by the agent at the end of every run)

> v9.1 (2026-11-24): كل حزمنا المعتمدة السبعة دُمجت في upstream؛ لا حزمة معلّقة للنشر.
> القواعد الدائمة في AGENTS.md / POLICY.md / METHODOLOGY.md؛ التاريخ في الأرشيف append-only.

## تحديث المرحلة 7 (2026-11-28) — triage v3 + الموجة ب + دمج الموجة أ الشامل
- **triage v3 [MEASURED]:** unsynth 164→140 (-24 محررة). apply_override_inner r60→r76، parse_field r54→r58.机会 جديدة: oci remove_path(r3). harvest-scans يستبدل قائمة كل كرارة بالكامل عند مسح جديد (لا دمج قديم).
- **الموجة أ مدموجة بالكامل [MEASURED]:** #373 oci human_size، #374 instance finish، #375 process EventPoll، #376 kv parse_controllers. main → e7885e4a. الحصيلة التراكمية 14 دمجة متتالية (#363–#376).
- **الموجة ب:** devices-random-xorshift ✅ PROVEN+مدفوع؛ fs-policy-identity-token-fnv1a ✅ PROVEN+مدفوع (أضافه البوت/جلسة موازية — أول مساهمة في fs-policy!)؛ vfs-copy-overlay-size-boundary أُصلح ثلاث مرات (مسار خاطئ → حجم Reader غير مطابق → FILE_SIZE=8 مطابق لـ Reader([u8;8])) وبانتظار الإثبات النهائي.
- **fs-policy/core محجوبان سابقًا لكن fs-policy فُتح عبر identity_token FNV-1a (دالة نقية).** core لا يزال محجوبًا (balanced_arguments_allowed مغطى بالاختبار الموجود @705–733).
- **R1/R2/R3 سارية؛ لم يُفتح أي طلب upstream آليًا.**


## تحديث المرحلة 7 (2026-11-28) — triage v3 + الموجة ب + إصلاح حزم البوت
- **triage v3:** تركيب multi-line delete-arm + fn-retval early-return. unsynth انخفض 164→140 (24 طفرة تحررت). المرشحون المؤهلون 51.
- **harvest-scans fix:** latest-run-per-crate يستبدل الناجيات القديمة بالكامل؛ لا تراكم عبر المسوحات (يمنع survives=false الكاذب).
- **fs-policy-identity-token-fnv1a:** ✅ PROVEN — أول مساهمة في ginux-fs-policy! تثبيت قيم FNV-1a المرجعية الدقيقة (طفرتا ^=→&=/|=). Spec-Ref: FNV-1a hash specification.
- **إصلاح حزم البوت:** devices-random-xorshift (بذرة خاطئة 1→0x6a09e667f3bcc909) وvfs-copy-overlay-size-boundary (FILE_SIZE غير معرّف → استدعاء مباشر بـ Entry). بانتظار إثبات الجولة الثانية.
- **الموجة أ:** #373 (oci) دُمج؛ #374/#375/#376 مفتوحة. أُرشفت oci من السجل.
- **devices/core:** معظم الدوال متعددة الطفرات مغطاة بالاختبارات الموجودة؛ devices-random-xorshift (بوت) هو المساهمة الوحيدة قيد الإثبات. core يحتاج مسحًا طازجًا أو دالة أخرى.
- R1/R2/R3 سارية؛ لم يُفتح أي طلب upstream آليًا.


## تحديث المرحلة 5 (2026-11-28) — ما بعد الدمج الشامل #363-#371
- **حدث [MEASURED]:** المالك دمج 9 طلبات في ~2 ساعة: #363-#369 (20:41-21:10Z) + #370 golden override-arms (22:40Z) + #371 oci select-manifest (22:48Z). main تقدّم 8b857786 → 0f08bd4c → **5ae0d435**. صفر مفتوحة.
- **vfs-decode-boundary-exact:** link-ge مثبت؛ path-eq كان مغطى بالاختبار الموجود @1211 (survives=false). استُبدل بـ link-eq (>→== لـ link_len) — فجوة decode حقيقية غير مغطاة. بانتظار إثبات العدّاء.
- **المصفوفة الحالية:** instance/oci مدموجة؛ vfs قيد الإثبات؛ process/kernel-views يحتاجان حصادًا طازجًا على 5ae0d435 (mutation-scan مُطلق لكل كرارة على حدة لتفادي سقف 25د).
- **Zero-Conflict Matrix:** reserve-proposals v2 نشط؛ الدفعة الخالية من التعارض تُحسب آليًا (واحد لكل ملف ولكل كرارة).
- **تدقيق fix/* (مرحلة 4):** لا علل src حقيقية في الدوال الحساسة المدققة؛ كل الناجيات نقص تغطية. R1/R2/R3 سارية؛ لم يُفتح أي طلب upstream آليًا.


## تحديث المرحلة 2+3 (2026-11-28) — البنية التحتية المثبتة والاحتياط المتنوع
- **المحرك:** prove-package.py v2 (anchor_count صارم، context-scoped، baseline_err + إيقاف مبكر، timeout=120) وauto-author.py v2 (JIT freshness على main الحالي، حقن mod-tests بمشي أقواس، إعادة توليد طازجة). اختبارات offline PASS؛ CI أخضر.
- **جسر الفرز:** triage-discoveries.py v2 يشتق ready_mutants جراحياً من (line,col) لـcargo-mutants على main الحالي (تفرد عبر نمو النافذة/context) + crate_balanced_top (أفضل 3 لكل كرارة). 55 مرشحاً مؤهلاً؛ الاستبعادات: cosmetic 16، stale 7، covered 46، unsynth 164.
- **الإثبات الحي [MEASURED run 46061682888]:** **7/7 حزم PROVEN** (baseline أخضر + طفرتان ناجيتان مقتولتان لكل حزمة، anchor_count موثق):
  instance-derive-grants · instance-validate-identifier · instance-override-id · instance-override-resources · process-pipe-ends-guards · **process-unshare-copy** · **kernel-views-cgroup-remove-busy**.
- **الاحتياط المدفوع على الفورك [MEASURED autopilot 46061805396 @ 20:11Z]:** 7 فروع tests/* جاهزة للفتح البشري (R1):
  `tests/instance-derive-grants` · `tests/instance-override-id` · `tests/instance-override-resources` · `tests/instance-validate-identifier` · `tests/process-pipe-ends-guards` · `tests/process-unshare-copy` · `tests/kernel-views-cgroup-remove-busy`.
  روابط الفتح: https://github.com/hafid-logic/ginux/pull/new/<branch> — العنوان والنص معبّآن مسبقاً من رسالة الcommit.
- **مخزون إضافي:** حزمة ذهبية table-driven `instance-override-arms-table` (4 أذرع match: workdir/environment/selective/catalog، 4 طفرات delete-arm_exact) في approved/pending بانتظار إثبات العدّاء.
- **تقييم unshare الأمني:** الطفرات الناجية في PipeSpace::unshare هي فجوة اختبارات ثوابت (عدّ الأعضاء/عتبة >1) وليست ثغرة عزل namespaces قابلة للاستغلال عبر API العام — لا مسار fix/* مطلوب هنا. الحزمة الاختبارية مثبتة.
- **القواعد:** R1/R2/R3 سارية؛ لم يُفتح أي طلب upstream؛ الفتح بيد المالك حصراً لكل بند.


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
  #320 (devices revoke-instance-scope، 13:54Z). **مفتوحة لنا 3/5 (السقف 5): #374، #375، #376 — كلها اختبارات خاصيات مُبرهنة بالطفرات (ناجيتان تُقتلان لكل حزمة). تفويض المالك: directives/v9.2-20261124.md.
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

- لا طلبات مفتوحة.
<!-- AUTO-OPEN-PRS:END -->

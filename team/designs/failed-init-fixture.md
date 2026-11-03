# failed-init-fixture — تصميم fixture للتأكيد الديناميكي لإفراج gate-22 (D9)

- **الحالة: تصميم فقط — لا تنفيذ** (توجيه v2.4-3، 2026-11-03). أي بناء قرار جديد من المستخدم.
- **الهدف:** إثبات ديناميكي end-to-end أن إصلاح gate-22 (PR #37 / issue #26) يُفرج فعلًا عن الإطارات الستة عندما يفشل init **بعد** قبول process_plan — اليوم: marker تسلسلي على فرع fork فقط (b04e7a74) + تحقق صيانة ساكن (hdae/gates-todo/22).
- **المرجع:** team/results/T-20261103-05 (ما بُني) + reports/2026-11-03.md §3 (لماذا البطاقة الأصلية غير قابلة ضمن «تغيير واحد + اختبار واحد»).

## ما يلزم (4 مكونات)

1. **ELF init مصنّع:** static-PIE سليم البنية يمرّ `published_rootfs::process_plan` (address_space.rs:259–292) ثم يفشل تنفيذيًا في نافذة stage-2 `directory_index ∈ {2,3}` (حوالي address_space.rs:425) ⇒ مسار الفشل **بعد** تخصيص الإطارات الستة ⇒ teardown ⇒ gate-22 ⇒ marker `ginux: Linux init hierarchy frames released after failed init` على المنفذ التسلسلي. (init بايتات فاسدة لا يصل — يُرفض مبكرًا قبل التخصيص، §3 سبب 2.)
2. **توصيل rootfs:** طبقة OCI تحوي الـELF المصنّع؛ دورة حياة domain عبر controller ABI (نمط test-c1/test-c2: controller-console.sh + container-config.sh) — وهذا فرع `configured_domain_uses_published_rootfs() == true` (lib.rs:4226) لا يجريه `make test` إطلاقًا (يقبل الملف التعريفي المضمّن فقط).
3. **أسلاك CI بلا شبكة:** بناء صورة OCI داخل الـrunner offline (مسارات OCI الحالية تنزّل من الشبكة وقت التشغيل — يخالف تصميمنا الحتمي)؛ فرع fork يحمل fixture + assertion في boot.sh على الـmarker على 10.0.13 و10.1.2.
4. **mutation check:** الـassertion يفشل على أساس قديم سابق لإصلاح #37 (أو مع إعادة `valid &&`) وينجح معه — إثبات إيجابي/سلبي عبر Actions.

## الجهد التقديري

2–4 جلسات مركزة (~6–12 ساعة): ELF + تغليف OCI (~نصف–1 جلسة)؛ تنسيق domain/controller في CI (1–2 جلسة)؛ assertion + تنقيح على النسختين (~نصف–1 جلسة). **هذه بنية تحتية لا «تغيير واحد + اختبار واحد».**

## المخاطر

- **زحف نطاق:** بنية OCI/controller تنافس خارطة طريق HDAE العلوية (مخالفة روح مهمتنا في AGENTS.md).
- **التعفن الصامت:** نافذة stage-2 وفحوص process_plan تفاصيل داخلية متغيرة في address_space.rs — أي تغيير علوي يكسر fixture بلا إنذار.
- **قيمة حدية:** gate-22 تحققها الصيانة ساكنًا؛ الإثبات الديناميكي تأكيد ضد انحدارات مستقبلية لا اكتشاف جديد.
- **يُثبت فرعنا لا upstream:** الـmarker ملك فرع fork؛ أي إرسال علوي يحتاج معادلًا يقبله الصيانة (وقاعدة POLICY: لا إعلان قبل البناء).
- **هشاشة TCG:** إقلاع domain في CI يضيف سطح توقيتات على النسختين (timeouts).

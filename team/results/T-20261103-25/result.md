# T-20261103-25 — فجوات اختبار الانحدار (دور gap-finder، W4)

التاريخ: 2026-11-03. المنهج: git فقط على /home/z/my-project/work/ginux-watch (upstream/main = 4c832ea6 [MEASURED-git])، بلا بناء ولا API. الآلية الحاكمة للاختبار في هذا المستودع: **(أ)** sanity boot — kernel يطبع سطر `ginux: …` بعد تحقق ذاتي (verify fn + `kernel_fail` عند الفشل) و`tests/qemu/boot.sh` يعمل `grep -q` على السطر؛ يعمل في CI عبر `.github/workflows/check.yml` → `make test`/`make test-qemu-smoke` [MEASURED: git show 4c832ea6:.github/workflows/check.yml]؛ **(ب)** اختبارات host `#[test]` داخل `mod tests` للكرات القابلة للاختبار مضيفًا فقط. درس F6: المترجم يرفض 20/30 bugs مزروعة في safe Rust و0 في unsafe/C [MEASURED: STATE.md سطر 17] ⇒ الاعتماد على type-safety غير كافٍ، وmutation check ضروري خصوصًا حيث الكود unsafe/C. درس D12: كرات no_std/UEFI (kernel) لا تقبل #[test] مضيفًا — اختبارها الوحيد هو boot-level أو extraction harness بمنهجية F9 [MEASURED: reports/2026-11-03.md §10.1].

## الجدول

| PR | issue | منطقة الإصلاح | اختبار انحدار جديد؟ | فجوة؟ | mutation check مقترح | قابلية التشغيل |
|---|---|---|---|---|---|---|
| #47 feca3fc | #22 | blocking socket polls (linux_socket.rs) | نعم — verify ذاتي بحدود قيم (None/0/1/1000/MAX) + kernel_fail + grep جديد في boot.sh [MEASURED] | لا | زرع: تغيير `bounded_timeout_poll_limit(Some(1)) == 1` إلى `== 0` في verify أو كسر clamp الدالة ⇒ متوقع: kernel_fail → غياب GINUX_KERNEL_OK → boot.sh يفشل | CI boot (make test) |
| #48 152be74 | #24 | secret process VM exclusion | نعم — print بعد تحقق `linux_mapping_secret_in_root` + grep جديد [MEASURED pairing]؛ عمق التحقق [INFERRED] | لا | زرع: إزالة شرط الاستثناء من copy ⇒ متوقع: فشل التحقق الداخلي/انقطاع السطر → boot.sh يفشل | CI boot |
| #49 9e7e298 | #25 | mprotect SMP shootdown (address_space.rs) | لا — بلا boot.sh، بلا print جديد، بلا #[test] [MEASURED: name-only + grep]؛ يعتمد على markers عامة سابقة (RELRO) لا تفرّق invlpg محلي عن shootdown عبر CPUs | **نعم** | زرع سطر واحد: استبدال `if !smp::invalidate_runtime_translation(page) {…}` بـ `asm!("invlpg [{}]", in(reg) page)` (العودة لحالة bug) ⇒ متوقع اليوم: **كل الاختبارات تنجح صامتة**؛ Check المقترح: static architecture-check (grep) يمنع `invlpg` حرفي في مسار `protect_current_linux_range_read_only` + marker عدّ acks عبر CPUs | make check (Actions host) للـstatic؛ boot test لا يفرّق السلوك [MEASURED: grep boot.sh@9e7e298] |
| #50 144d811 | #28 | runtime DMA quarantine | نعم — quarantine fail-closed + grep جديد [MEASURED pairing] | لا | زرع: السماح بإعادة استخدام FrameLease بعد retirement فاشل ⇒ متوقع: فشل marker/grep | CI boot |
| #51 8232ab5 | #29 | IOMMU rollback quarantine | نعم — marker حاسم `failed IOMMU activation rollback quarantined` + grep [MEASURED] | لا | زرع: السماح بretirement بعد rollback غامض ⇒ متوقع: انقطاع marker → فشل | CI boot |
| #52 b4628fc | #20 | gzip/unpack bound (image_store) | نعم — policy verify + grep جديد [MEASURED pairing] | لا | زرع: رفع سقف التوسع/تجاوز policy ⇒ متوقع: فشل verify الداخلي → boot fails | CI boot؛ نواة no_std ⇒ لا host #[test] (منطق D12) |
| #59 0fcd263 | #57 | Linux lazy-page quota | **جزئي** — verify ذاتي `verify_linux_domain_owned_runtime_page_metadata` + kernel_fail موجودان [MEASURED: lib.rs:1862-1866@0fcd263] لكن **boot.sh لا يassert سطر النجاح** [MEASURED: git grep 'runtime page metadata' 0fcd263 -- tests/ ⇒ فارغ]؛ ملف الgate بقي في gates-todo/ | جزئية | زرع: حذف كتلة `if !address_space::verify_…{kernel_fail}` ⇒ اليوم: **نجاح صامت**؛ Check: إضافة grep لسطر `domain-owned Linux runtime page metadata validated` في boot.sh ثم الزرع نفسه ⇒ متوقع: فشل boot.sh | CI boot (make test جاهز، سطر واحد) |
| #70 277187f | #62 | sync poll budget (poll/ppoll/select) | نعم — print + grep جديد بنمط #47 [MEASURED pairing] | لا | زرع: كسر budget الدالة ⇒ متوقع: فشل verify → kernel_fail | CI boot |
| #73 5dd58ca | #63 | registry DNS entropy + إزالة fallback | لا — صفر #[test] في registry.rs قبل وبعد [MEASURED]، crate `services/network` `test = false` في Cargo.toml [MEASURED]، بلا boot.sh ولا kernel print للentropy [MEASURED: grep boot.sh@5dd58ca ⇒ فارغ] | **نعم** | زرع سطر واحد: `let Some(interface_entropy) = tls_seed()` → `let interface_entropy = Some(FIXED_SEED);` ⇒ اليوم: **نجاح صامت**؛ Check: F9-host harness يستخرج منطق tls_seed/entropy-binding إلى crate مضيف + boot.sh grep لmarker entropy ناجح جديد (يتطلب print من upstream) | Actions host harness (نمط fuzz-branch-verify عندنا) أو boot-level |
| #54 6324692 | #43 | overflow-checks في release profile | نعم — `#[test] #[should_panic] release_profile_traps_size_overflow` جديد في crates/oci + ربطه في make check بـ`cargo test --release` [MEASURED: diff Cargo.toml/Makefile/lib.rs] | لا (للprofile) / جزئية (لملفات النواة) | زرع: حذف `overflow-checks = true` من [profile.release] ⇒ متوقع: should_panic لا يهلع ⇒ make check يفشل فورًا | make check — Actions host، أرخص check في القائمة |
| #81 4c832ea6 | #62-access | mmap descriptor access modes (cpu.rs +115 سطر، 0 unsafe) [MEASURED] | نعم — `verify_linux_mmap_access_modes()` + grep جديد `Linux mmap descriptor access matrix validated` [MEASURED] | لا | زرع: قلب شرط access-mode في المصفوفة ⇒ متوقع: فشل verify → boot fails | CI boot |

الإحصاء: 8 نعم / 1 جزئي (#59) / 2 فجوة مؤكدة (#49، #73) [MEASURED من الـdiffs].

## أعلى فجوتين أولوية (security-first)

1. **#49 (issue #25 — mprotect SMP shootdown)**: عكس الإصلاح بسطر واحد (`invlpg` محلي بدل shootdown مُقرّ عبر CPUs) يمرّ بكل CI صامتًا — ومرفوض 0% من المترجم لأنه unsafe asm [MEASURED: grep الdiff + F6]، وهو عيب سلامة ذاكرة/أذونات (صفحة believed read-only تبقى writable في TLB آخر CPU) ⇒ الأعلى خطورة بين الفجوتين.
2. **#73 (issue #63 — registry entropy/DNS fallback)**: لا سطح اختبار إطلاقًا (crate `test=false`، بلا markers)؛ زرع seed ثابت أو إعادة DNS fallback لا يُلاحَظ، وentropy/fallback عيب أمني شبكي مباشر.

**قرار builder مقترح (للمستخدم، لن أبني):** نعم — بطاقة واحدة تستحق: **#49** لأن mutation check الخاص بها (architecture-check سطري + marker acks) رخيص، CI-قابل عبر `make check`/`make test` الموجودين، ويغلق أعمق ثغرة رصد؛ #73 يمكن تغطيته لاحقًا بنفس البطاقة كمرحلة ثانية (F9 harness).

## حدود التحليل

التحليل بنيوي من الـdiffs فقط: أثبتُّ [MEASURED] وجود/غياب pairing بين print وgrep و#[test]، وربط make-targets بـCI، لكن **لم أشغّل أي boot أو mutation** (بناء ممنوع) ⇒ عبارات "متوقع: يفشل/يصمت" [INFERRED] من قراءة مسارات التحكم (kernel_fail → غياب GINUX_KERNEL_OK → فشل boot.sh)، وعمق بعض verify الداخلية (#48/#50/#52) لم يُدقَّق سطرًا سطرًا. الخلايا "لا فجوة" تعني وجود اختبار جديد يمنع انتكاس *العيب المحدد*؛ لا تدعي تغطية سلوك مجاور. بطاقات gates-done (hdae/) ادعاءات المؤلف وليست إثباتًا مستقلًا. ولا نفوق لاحق: 6 من 8 assertions نمط marker تراقب *وجود* self-check أكثر من *سلوكه* — mutation يحذف الاستدعاء مع إبقاء print يمرّ صامتًا في النمط كله، وهذه ملاحظة عامة موثقة هنا لا فجوة لكل بند.

## مسارات

- evidence/test-diff-scan.txt — لكل دمج: name-only + test-marker hits أو "none found".
- meta.json — duration/tools/status.

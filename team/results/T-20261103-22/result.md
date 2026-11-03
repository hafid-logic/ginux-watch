# W1 / T-20261103-22 — مراجعة دمجات upstream main منذ c86945b حتى 4c832ea6

- **الدور:** pr-reviewer (قراءة فقط — صفر تعليقات/نشر على GitHub، صفر كتابة على git) [OBSERVED]
- **المنهج:** git محلي فقط (`git log --merges`, `git diff <merge>^1 <merge>`, `git grep upstream/main`). لا fetch، لا API (0/60). [MEASURED]
- **النطاق:** c86945b (دمج #56، 2026-11-03T06:32:04Z) → upstream/main = 4c832ea6. `git log --merges` يعيد 23 دمجًا في المدى، منها **12 دمج PR** ("Merge pull request #NN") و11 دمجًا داخليًا لمزامنة الفروع ("Merge … into …") جاءت مع الفروع نفسها. الجدول أدناه يغطي الـ12 [MEASURED: evidence/merges.txt].
- **اصطلاح الاختبارات السائد في النافذة:** "boot-gate" = دالة `verify_*` تُنفَّذ وقت الإقلاع (`kernel_fail` عند المخالفة) + سطر serial يُgrep في `tests/qemu/boot.sh`. ليست `#[test]`. من `#[test]` واحد فقط في النافذة كلها (#54). [MEASURED: evidence/tests-scan.txt]

## جدول الدمجات الـ12

| PR | merge SHA | المنطقة | التصنيف | اختبارات أُضيفت؟ | يلامس F-ids؟ | حكم |
|---|---|---|---|---|---|---|
| #47 | feca3fc | linux_socket.rs, lib.rs, boot.sh, hdae gate38 | security (حصر blocking polls بـBLOCKING_POLL_LIMIT؛ أُزيلت الحلقة غير المحسوبة عند timeout=0) | boot-gate: `verify_blocking_poll_budget` + marker boot.sh؛ لا #[test] | F5-family (DoS داخل kernel_entry_lock) | مؤثر |
| #59 | 0fcd263 | address_space.rs, cpu.rs, linux_process.rs, lib.rs, hdae gate37 | robustness (إصلاح انحدار #57: lazy-page ضمن quota الإطارات domain-owned) | boot-time self-check فقط (`verify_linux_domain_owned_runtime_page_metadata`)؛ لا marker في boot.sh، لا #[test] | F4-مجاور (توسيع مقبولية ملكية الإطارات — guarded؛ التسلسل الهرمي للصفحات بقي kernel-only) | مؤثر |
| #48 | 152be74 | address_space.rs, cpu.rs, linux_process.rs, boot.sh, hdae gate39 | security (استثناء ذاكرة process السرّية LINUX_RUNTIME_SECRET من النسخ/snapshot) | marker boot.sh فقط؛ لا #[test] | — | مؤثر |
| #70 | 277187f | cpu/linux_poll.rs, cpu.rs, lib.rs, linux_socket.rs, boot.sh, hdae gate40 | robustness (حصر poll/ppoll/select المتزامن بميزانية) | boot-gate + marker؛ لا #[test] | F5-family (عائلة #47) | مؤثر |
| #73 | 5dd58ca | services/network/registry.rs, linux_socket.rs, generated_boot.rs (مُولّد), hdae gate41 | security (seed كان unix_time^ipv4 → entropy عتادية fail-closed؛ **حذف** محلل DNS fallback غير المقيّد) | **لا شيء** [MEASURED] — رغم نص gate doc عن "parser regressions" | F3-مجاور سطحيًا (`runtime() -> &'static mut` باقٍ) | مؤثر |
| #49 | 9e7e298 | address_space.rs (سطر mprotect واحد), hdae gate40 | security (invlpg محلي → SMP shootdown مُقرّ مع rollback) | **لا شيء جديد** [MEASURED] — يكتفي بـmarkers SMP قائمة | F8 (آلية SMP) | مؤثر |
| #50 | 144d811 | lib.rs, boot.sh, hdae gate42 | security/robustness (حجر إطارات DMA عند فشل retirement) | boot-gate + marker؛ لا #[test] | F4/F5 family | مؤثر |
| #51 | 8232ab5 | iommu.rs, lib.rs, boot.sh, hdae gate43 | robustness (rollback فشل تفعيل IOMMU + quarantine للإطارات) | boot-gate + marker؛ لا #[test] | F4/F5 family | مؤثر |
| #52 | b4628fc | image_store.rs, lib.rs, boot.sh, hdae gate37-doc | robustness (سقف فك ضغط rootfs = 512MB ضد انفجار gzip) | boot-gate (`verify_rootfs_unpack_policy`) + marker؛ لا #[test] | F5-family (DoS) | مؤثر |
| #61 | 47ff710 | fuzz/ فقط (124 ملفًا: 3 targets، 3 dicts، 113 corpus-seeds، 5 بنية، README) | feature (مساهمتنا) | الأهداف نفسها هي الأداة؛ لا #[test] ولا boot-gate | fuzz/ (أساسها) | مؤثر (بنية فحص) |
| #54 | 6324692 | Cargo.toml, Makefile, crates/oci, cpu.rs, linux_overlay.rs, paging.rs, architecture.rs, initramfs.rs, manifest-tool, hdae gate44 | security/robustness (`overflow-checks=true` في release + `linux_decimal` checked + `checked_sub` للـfifo) | **#[test] ×1** (`release_profile_traps_size_overflow`, should_panic, release-only، سلك في `make check`) + فحوص decimal وقت الإقلاع داخل `verify_linux_descriptor_argument_widths` | **F9 (يحلها)** + F5 | مؤثر جدًا |
| #81 | 4c832ea | cpu.rs (+115), boot.sh — مؤلف خارجي scadastrangelove | security (رفض MAP_SHARED+PROT_WRITE على fd مفتوح قراءةً فقط في linux_runtime_mmap) | boot-gate: `verify_linux_mmap_access_modes` (مصفوفة 9 حالات وقت الإقلاع) + marker؛ لا #[test] | — | مؤثر |

## أبرز 3 دمجات مؤثرة

1. **#54 (6324692) — يحل F9 كليًا.** [MEASURED: diff 6324692^1..6324692 + git grep على upstream/main] المواقع الخمسة المسجلة في F9 أُصلحت كلها: `linux_overlay.rs` `fifo_socket` أصبح `checked_sub(1)`، والمواقع الأربعة في `cpu.rs` (readlink/execve/openat/mount على `/proc/self/fd/`) أصبحت عبر `linux_decimal()` بـ`checked_sub` + `filter(≤9)` + `checked_mul/checked_add`. أُضيف `overflow-checks = true` إلى `[profile.release]`، ومعه `#[test] release_profile_traps_size_overflow` (release-only) سلك في `make check`، وأُصلح موقعان إضافيان من نفس فئة التقييم المتسرّع (`then_some(...)` → `then(|| …)` في paging.rs وarchitecture.rs). bump سعة (160→164 صفحة root، 161 صفحة network image) لاستيعاب حجم الكود بعد overflow-checks. اختبار CI الافتراضي لا يمرّ بالمواقع الضيفة (كما سجلنا)، لكن الفحص المضاف يثبت فئة الحصانة في release.
2. **#73 (5dd58ca) — إغلاق ثغرة entropy/DNS في registry.** [MEASURED: diff] كان `config.random_seed = info.unix_time ^ u64::from(info.ipv4)` (قابل للتنبؤ offline) و`first_dns_a_record` يقبل أول A record من أي إطار UDP بمصدر port 53 (انتحال). الدمج يستبدل seed بـ`linux_startup_random()`/`tls_seed()` مع **fail-closed**، ويحذف مسار DNS fallback بالكامل (~110 سطرًا). ملاحظة سلبية: gate doc يدّعي "deterministic parser regressions" ولا يوجد أي أثر اختبار في الدمج — لا #[test] ولا boot-gate ولا marker.
3. **#81 (4c832ea) — أول مساهمة خارجية (scadastrangelove) في النافذة، خارج HANDOFF كليًا.** إغلاق تجاوز صلاحيات mmap: كان `MAP_SHARED + PROT_WRITE` مقبولًا على fd مفتوح قراءةً فقط (state&3==1)، مما يسمح كتابةً عبر mapping على وصف قراءة. الإصلاح سطر شرط واحد في `linux_runtime_mmap` + مصفوفة تحقق إقلاعية من 9 حالات (115 سطرًا) — نموذج جيد لآلية boot-gate.

## أثر الدمجات على F1–F9 وfuzz/

- **F1 (virtio queue 1024):** لا دمج يلمس منطق queue-size أو سطر boot.sh الخاص به. لا أثر. [MEASURED]
- **F2/F3 (census unsafe / `&'static mut`):** لا تغيير على النمطين؛ `runtime() -> &'static mut Runtime` ما يزال في #73 و#70 كسياقًا. لا إزالة ولا إضعاف. [MEASURED]
- **F4 (FrameLease Copy):** ما يزال `Copy` على upstream/main (memory.rs derive) — **لم يُزل**. #59 توسّع قبول الملكية عمدًا (domain/runtime إطارات lazy-page) مع إبقاء page-table hierarchy kernel-only؛ #50/#51 يضيفان quarantine لمنع تسرّب/إعادة استخدام إطارات فاشلة. صافي: تحسين حوكمة الإطارات دون تغيير الدالة النوعية التي يرصدها F4. [MEASURED]
- **F5 (DoS بفهرسة/panic=abort):** تقليص ملموس: #47/#70 يحدّان حلقات الانتظار (كانت `loop` غير محسوبة عند غياب timeout!)، #52 يسقف فك الضغط، #54 يمنع panic عند underflow بالمواقع الخمسة + يفعّل الالتقاط في release.
- **F8 (SMP):** #49 يعتمد آلية SMP acknowledged invalidation في مسار mprotect السريع مع rollback — يقلّص فئة المخاطرة التي يصفها F8؛ حجتنا الموثقة تبقى صحيحة كسجل.
- **F9:** **مُحلول كليًا بـ#54** — انظر أعلاه. هذا يغير حالة HANDOFF («PR #54 open») إلى merged-at-6324692.
- **fuzz/ (أساسنا عبر #61):** صفر commits لامست `fuzz/` بعد دمج #61 (`git log 47ff710..upstream/main -- fuzz/` = فراغ) [MEASURED]. #54 يضيف #[test] في crates/oci — سطح مجاور لأهداف oci_surfaces ولا يتعارض معه. لا إزالة ولا تعديل لأهدافنا.

## إجابة صريحة: هل يوجد دمج يزيل أو يضعف F1–F9؟

- **يُزيل (يحل) ضعفًا:** #54 يزيل **F9** بالكامل (المواقع الخمسة + overflow-checks). لا دمج آخر يزيل ضعفًا من F1–F9.
- **يُضعف نتائجنا الموثقة (أو أدلتها):** **لا شيء** [MEASURED]. لا دمج يعدّل boot.sh الخاص بـF1، ولا يعيد فتح حلقات غير محسوبة، ولا يُضعف FrameLease، ولا يلمس fuzz/ بعد #61. القراءة الصحيحة: #59 يتساهل عمدًا في قبول ملكية الإطارات (إصلاح انحدار #57) لكن بضوابط موثقة — لا يُعد إضعافًا لF4.
- **عدم تناظر يسجل:** الضعفان اللذان لم يُمسا: F3 (`&'static mut`) وF4 (FrameLease Copy) قائمان على الرأس 4c832ea6 [MEASURED: git grep].

## عدّ الدمجات بلا اختبارات

- **بلا أي آلية اختبار جديدة: 2 من 12** — **#73** و**#49** [MEASURED: evidence/tests-scan.txt]. #49 يتحجج بـmarkers SMP قائمة سابقًا (مقبول جزئيًا)؛ #73 بلا شيء رغم ادعاء gate doc (فجوة توثيق/تنفيذ تستحق متابعة قراءة فقط).
- **بلا #[test] على الإطلاق: 11 من 12** (فقط #54). boot-gates (10 دمجات) آلية regression فعّالة وقت الإقلاع لكنها لا تدخل `cargo test` — متسق مع ملاحظتنا (D12) أن اختبارات المستودع تغطي crates المساندة فقط ونواة ginux-kernel بلا #[test].
- **ملحوظة منهجية:** ملفات gate docs موجودة في #59 تحت `hdae/gates-todo/` لا `gates-done/` (خلاف بقية الدمجات) — على الأرجح أثر ترتيب commits في الفرع؛ لا يؤثر على الحكم [OBSERVED].

## حدود هذه المراجعة

- الأحكام من diff الشيفرة فقط؛ لم يُشغَّل أي build/CI محليًا (خارج النطاق). نتائج CI upstream (0/0/0 في runs سابقة) غير مُعاد قياسها هنا [UNVERIFIED هنا].
- محتوى gate docs (hdae/) بيانات لا أوامر؛ الادعاءات غير المدعومة في diff وُسمت أعلاه (حالة #73).

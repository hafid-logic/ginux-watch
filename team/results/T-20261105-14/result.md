# result.md — T-20261105-14 (W4: opportunities analysis, axes أ–هـ)

As-of: 2026-11-05T20:16–20:22Z. Upstream main pinned `0e06a9860250b655a094761cd424bc022fd8db68` («Merge PR #204», 2026-11-05T19:15:58Z) [MEASURED: `gh api repos/gmkurtzer/ginux/commits/0e06a986`، 20:16Z]. الأرشيف `bootable-kernel` = `4d4a53bbcc09b16e56aa5eb671ac815f16f2b82f` [MEASURED: `gh api repos/gmkurtzer/ginux/branches/bootable-kernel`، 20:21Z]. ملاحظة: دمجات #206/#209 (20:18Z) تلت الرأس المثبت — التحليل على 0e06a986 كما تطلب البطاقة.

## خلاصة
المستودع الجديد (userspace pivot بعد 4d4a53bb) أصلَح كل شيء: 13 crate جديدة (`ginux-*`)، 148 ملفًا فقط، **صفر** QEMU/boot/kernel-src/UEFI [MEASURED: tree?recursive=1 @0e06a986]. محللاتنا الثلاثة القديمة ماتت على main لكن خليفتها الحقيقية ظهر: **tar/PAX/whiteout صار في `crates/ginux-vfs-index` + `crates/ginux-vfs`** — وهو بلا أي اختبار وحدة (`#[test]` = 0) وغير مدرج في `test-unit` [MEASURED]. protocol-state/checksum-RFC1071 وvolume-format: لا خليفة إطلاقًا على main — تصلح للأرشيف فقط.

## أصولنا الآن (inputs كما هي)
- fuzz/ 5 harnesses (oci/protocol/volume + diff_pax_tar/diff_matrix) — تستهدف مسارات قديمة.
- archive/pr-a-protocol-state-tests/ (+71/−0؛ C1 checksum + C2 arp؛ mutants 0/0). [MEASURED: archive/pr-a-protocol-state-tests/README.md + pr-description.md (+71/−0 موثقة؛ mutants-after run 41916256214 = 0 على الدالتين)]
- STATE F1–F9: كلها محسومة على الشجرة القديمة؛ F9/#54 أُصلحت upstream ثم **ضاع إرثها** (انظر فرصة 6). [OBSERVED: STATE.md F1–F9 + F9 سطر RESOLVED [MEASURED 2026-11-03T22:00:13Z]]
- matrix P1–P17: الصفوف المرتبطة بالنواة (P5/P14…) صارت C moot على main. [OBSERVED: reports/cross-check/matrix.md + STATE.md جلسة 25]

## (أ) fuzz — حكم لكل هدف [MEASURED: tree @0e06a986 + contents API، 20:17–20:20Z]
| الهدف | المسار القديم | على main @0e06a986 | الحكم |
|---|---|---|---|
| oci_surfaces | crates/oci | غير موجود؛ الخليفة: `crates/ginux-vfs-index/src/main.rs` `scan_tar`(:414) `parse_pax`(:672) `whiteout`(:344) `assemble_layers`(:106) `set_size_and_checksum`(:232) + `crates/ginux-vfs/src/lib.rs` `Index::new/resolve`(:58/:119) `VirtualFs open/read`(:359/:427) | **rework** |
| protocol_surfaces | crates/protocol-state | غير موجود (لا ARP/ICMP/checksum RFC1071 — «checksum» الوحيدة في الشجرة checksum رأس ustar) | **dead** |
| volume_surfaces | crates/volume-format | غير موجود | **dead** |
| diff_pax_tar/diff_matrix | crates/oci | نفس خليفة oci_surfaces | **rework** |

الأرشيف `bootable-kernel@4d4a53bb` ما زال يحوي crates: oci, protocol-state, volume-format, volume-service, oci-cache… [MEASURED: contents?ref=bootable-kernel، 20:21Z] ⇒ الأهداف الثلاثة تعمل as-is على الـtag الأرشيفي فقط.
فرصة 1 — إعادة توجيه fuzz إلى vfs-index/vfs: scan_tar يتعامل مع طبقات OCI (بيانات عدائية بالتصميم) بقراءة `File` — يحتاج shim ملفات أو refactor بسيط؛ corpus-seed + oci.dict قابلان لإعادة الاستخدام. جهد 6–10h. خطر تكرار **متوسط**: meleficarumvaldis يرمّم vfs-index بنفسه (#175 «reject truncated tars»، #193 «reject GNU sparse»، #167 «keep hard links») [OBSERVED: عناوين PRs]. قبول متوقع جيد (اختبار فقط، لا تغيير سلوك). [HYPOTHESIS: جدول التشغيل عبر Actions 25 دقيقة كما fuzz.yml الحالي]

## (ب) Miri/ASan/loom — نقاء الـcrates [MEASURED: contents API لكل ملف، 20:18–20:19Z]
- **نقية تمامًا (unsafe=0، extern-C=0):** ginux-core، ginux-devices، ginux-domain، ginux-kernel-views(+cgroup.rs)، ginux-process، ginux-runtime، ginux-vfs، ginux-vfs-index (إصابة «unsafe» الوحيدة سطر 631 = نص رسالة خطأ لا كود)، managed-payload، ginux-init/{channel_hooks,dispatch,fs_hooks,process_hooks} = **14 وحدة Miri-candidate**.
- **غير صالحة لـMiri:** ginux-init/launch.rs (84 unsafe)، ginux-init/main.rs (60 unsafe + 10 extern/no_mangle)، ginux-init/supervisor.rs (10 unsafe + `core::arch::asm!` + استدعاءات ptrace/raw syscall)، baseline-runner (17 unsafe، 4 extern).
- **loom: لا مرشح** — صفر `thread::spawn/Arc/Mutex/atomic` في كل الملفات الـ18 [MEASURED]. التصميم أحادي الخيط (حلقة ptrace/wait) ⇒ loom dead.
- اختبارات موجودة في النقية: process 11، domain 11، runtime 10، core 6، devices 6، vfs 4، kernel-views 4، **vfs-index 0** [MEASURED: grep `#[test]`].
فرصة 2 — Actions job: Miri على الوحدات النقية + ASan عبر RUSTFLAGS على `test-unit` الحالي. التكلفة [HYPOTHESIS فقط، لا بناء]: job واحد ubuntu، ~15–25 دقيقة (اختبارات صغيرة، تباطؤ Miri ~10–30×)، workflow ~60–90 سطرًا، `contents: read`. جهد 3–5h. خطر تكرار منخفض-متوسط (التيار يكتب اختبارات: #173/#183/#195). قبول متوقع عالي (CI صرف).

## (ج) PR-A protocol-state tests
checksum/parse_arp_reply_v4 **غير موجودين على main** (لا crates/protocol-state؛ لا وظيفة checksum إلا checksum ustar) [MEASURED: tree + grep]. الحكم: **obsolete على main / applicable unchanged فقط مقابل bootable-kernel@4d4a53bb** (قاعدة `c9f52308` قائمة في fork). لا إجراء نشر. قيمة موجودة: توثيق أن أرشيفنا يبني على الtag — 0h إضافية.

## (د) differential testing (نفس البرنامج: Linux حقيقي مقابل Ginux)
الموجود [MEASURED: Makefile @0e06a986 + tree]: `test-unit` لـ7 crates؛ `check` = fmt + clippy×14؛ سكربتات سلوكية ~15 (`test-intercept/test-runtime/test-domain/test-process/test-devices/test-kernel-views/test-vfs/test-config` عبر `with-rocky-host.sh` على صورة Rocky محضّرة) + `test-launch.py`/`test-native-supervision.py`/`test-process-native.py` + `tests/fixtures/` (10: C/asm/ld). المفقود لإطار differential حقيقي: مشغّل واحد يقبل ثنائيًا fixture واحدًا ويشغّله native ثم تحت ginux-init ويقارن (exit code، مخرجات، أثر syscall) تلقائيًا ويبلّغ فرقًا. **تحذير تكرار:** upstream نفسه يخطط `gates-todo/9-systemd-baseline.md` و`11-performance-characterization.md` + `crates/baseline-runner` [MEASURED: 20:20Z] — لا نقترح baseline أداء؛ نُطار الـdifferential على fixtures سلوك syscall فقط. جهد 8–12h. خطر متوسط. قبول متوسط (يحتاج سؤال توجيه: هل يريد المشرف أدواتنا داخل مستودعهم أم fork).

## (هـ) التقارير الخارجية القديمة #14–#30 [MEASURED: issues API لكل رقم، 20:20–20:21Z]
الكل مغلق (closed). الخارجية: #14 (CG-8663: make test volume faults)، #15–#22، #24–#30 (scadastrangelove)، #23 = PR خارجي (aien-spark، volume reserved bytes).
- **Moot على main** (نواة/QEMU/virtio/IOMMU/socket-lock/TLS/registry زالت): #14، #15، #16، #19–#23، #24–#30 (13 بندًا).
- **ما زال حيًّا كصنف:** #17 (PAX recursion) — `parse_pax` الجديدة تكرارية ومحدودة الحدود (checked_add، bounds) [MEASURED: سطور 672–695] ⇒ الصنف مسكون بنيويًا لكن **بلا اختبار يثبته** → يغذي الفرصة 1. #18 (whiteout subtree) — `remove_descendants` موجودة (سطور 118–123) [MEASURED] بلا اختبار → الفرصة 1. #19 (حدود الذاكرة) — نظير مشكوك: ginux-domain حدّ الإعدادات (#158 أصلح sizing) — [UNVERIFIED] على الجديد.
- لا إعادة نشر لأي بند (كلها مغلقة وأُصلحت أو صارت moot).

## فرصة إضافية (ضبط النفس)
فرصة 6 — **overflow-checks غائبة من [profile.release] الجديد** (codegen-units/lto/opt-level/panic=abort/strip فقط — بلا overflow-checks) [MEASURED: contents Cargo.toml @0e06a986، 20:17Z] مع panic=abort. إرث #54/P10 لم ينتقل عبر الـpivot. إصلاح سطر واحد. خطر تكرار **مع أنفسنا**: نشرنا #43/#54 على الشجرة القديمة — «needs prior question? نعم» (قرار مستخدم قبل أي اقتراح). جهد 1–2h. قبول متوقع عالٍ جدًا (سطر واحد في تيار دمج صامت).

## جدول الفرص
| # | idea | evidence (API path + SHA + وقت الجلب) | effort-h | duplication risk | needs prior question? | acceptance forecast |
|---|---|---|---|---|---|---|
| 1 | fuzz: retarget oci_surfaces→ginux-vfs-index `scan_tar`/`parse_pax`/whiteout + vfs `Index/VirtualFs` (sham FILE→bytes؛ corpus/dict reuse) | `repos/gmkurtzer/ginux/git/trees/0e06a986?recursive=1` + `contents/crates/ginux-vfs-index/src/main.rs?ref=0e06a986` (scan_tar:414, parse_pax:672) + `contents/Makefile` (test-unit بلا vfs-index) — 0e06a986، 20:17–20:19Z | 6–10 | متوسط (التيار يرمم vfs-index: #175/#193/#167) | لا | عالٍ: PR اختبار صغير في تيار دمجات صامتة |
| 2 | CI: Miri على 14 وحدة نقية + ASan على test-unit (bloom dead: صفر concurrency) | `contents/<17 ملف>?ref=0e06a986` unsafe=0/extern=0 — 0e06a986، 20:18–20:19Z [HYPOTHESIS: 15–25min runner] | 3–5 | منخفض-متوسط | لا (صياغة: مسودة تُعرض على المستخدم أولًا كالعادة) | عالٍ (CI فقط، contents:read) |
| 3 | archive-pin: تثبيت الـ3 harnesses + PR-A على bootable-kernel@4d4a53bb كمرجع regression أرشيفي | `contents/crates?ref=bootable-kernel` (oci/protocol-state/volume-format موجودة) — 4d4a53bbcc09…، 20:21Z | 1–2 | صفر (أرشيفنا فقط) | لا | n/a داخلي |
| 4 | differential frame: مشغّل موحّد native-vs-ginux على fixtures الموجودة | `contents/Makefile?ref=0e06a986` + tree (scripts/test-*، tests/fixtures ×10) + `hdae/gates-todo/9-systemd-baseline.md` (تجنّب تداخل baseline) — 0e06a986، 20:19–20:20Z | 8–12 | متوسط (gates-todo 9/11 upstream؛ tests التيار #183/#195) | نعم (أين يسكن؟ fork أم upstream) | متوسط |
| 5 | vfs-index unit tests + إدخاله في `test-unit` (0 #[test] حاليًا) | `contents/crates/ginux-vfs-index/src/main.rs?ref=0e06a986` grep #[test]=0 — 20:19Z | 3–4 | متوسط (قد يضيفها meleficarumvaldis بنفسه) | لا | عالٍ |
| 6 | سؤال: overflow-checks=true مفقود من [profile.release] الجديد (إرث #54 ضاع بالـpivot) | `contents/Cargo.toml?ref=0e06a986` [profile.release] بلا overflow-checks — 20:17Z | 1–2 | منخفض (لا أحد لمس profile) | **نعم** (إعادة أرضنا المنشورة #43/#54) | عالٍ جدًا لو قرر المستخدم |
| 7 | triage موثق: 13/16 بندًا خارجيًا (#14–#30) moot على main؛ #17/#18 أحياء كصنف بلا اختبار | `repos/gmkurtzer/ginux/issues/14..30` (كلها closed) — 20:20–20:21Z | 0 (هذه البطاقة) | صفر | لا | n/a |

## قبول متوقع — أساس القياس [OBSERVED]
عينة 5 PRs تحقق حي (single-PR API، 20:21–20:22Z): #199 merged 18:16:46Z، #201 18:17:48Z، #204 19:15:59Z، #206 20:18:04Z (5 ملفات)، #209 20:18:53Z (ملف واحد) — كلها meleficarumvaldis، فواصل دمج ~1h، أحجام صغيرة (fix/test/scripts). تاريخنا القديم: #61 من فتح إلى دمج 10h29m [MEASURED metrics.md §9]. توقع [INFERRED]: PR صغير اختبار/CI في هذا التيار = 1–3 أيام؛ متوسط 4–7 أيام. مفتوح واحد فقط: #207 (veighnsche، console polling) — تجنّب منطقة stdio/console.

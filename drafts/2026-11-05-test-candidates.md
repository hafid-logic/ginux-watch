# مرشحو «اختبار صرف» — توجيه v3.3 §4e (2026-11-05)

> الحالة: هيكل مبدئي — قسم 4d مبني على dump 2026-11-05 (78 PR)؛ قسم 4e يُملأ بعد
> اكتمال run الـ feasibility (llvm-cov/mutants/clippy) عبر Actions. لا بناء، لا فرع، لا نشر.

## 4d) بوابة التكرار من dump (2026-11-05)

### 4d.0) نبذة عن الـ dump وحدود البيانات

- `pulls-all-2026-11-05.json` يحوي **78 PR** بحالة `state=all`؛ **كلها `state=closed`** —
  **صفر PR مفتوحة** (61 `merged_at != null`، و17 مغلقة غير مدموجة، و1 بحالة `draft=true` وهي
  #3 المغلقة «WIP: Define feedback-driven hardening research»). [jq `group_by(.state)` على
  inbox/upstream-dump/pulls-all-2026-11-05.json]
- نطاق الأرقام في الـdump: **#3 → #151**؛ `pulls-files-all-2026-11-05.json` يحوي 644 سجل
  ملف تغطي نفس الـ78 PR (78 مجموعة `pr` فريدة). [jq على الملفين]
- **حدود الحقول (معلنة لا مخمَّنة):** حقول `additions`/`deletions`/`changed_files` في
  pulls-all كلها **null** — كل أرقام الأسطر/عدّ الملفات في هذا القسم **مشتقة من جمع
  pulls-files-all** لكل PR. كذلك `user.login` و`head.ref` مُبسَّطان في الـdump إلى نصين
  (`user`, `head`). [فحص jq للمفاتيح]
- **قيد استنتاج «اختبار صرف» من الـdump:** البيانات أسماء ملفات فقط؛ كتل `#[cfg(test)]`
  داخل `src/lib.rs` **لا تُرى من أسماء الملفات**. الإشارات المستخدمة هنا: ملفات تحت
  `tests/`، ملفات باسم `*_test*`/`*tests*.rs`، فروع تبدأ بـ`test/`، عناوين تبدأ بـ«Test».
  حيث لا تنطبق إشارة نقول صراحةً «غير محدد من الـdump».

### 4d.1) موجة المساهم الخارجي meleficarumvaldis — 33 PR

**الإجمالي: 33 PR** (المصدر: pulls-all-2026-11-05.json، `user == "meleficarumvaldis"`)،
في موجتين أنشئتا يوم 2026-11-04: **#87–#99** (8) ثم **#125–#149** (25).
**23 مدموجة** و**10 مغلقة غير مدموجة** (`merged_at=null`) — لا واحدة منها `open`.
تشمل PRs سابقة على #140 كما طلب التوجيه: **#87, #88, #90, #91, #93, #95, #97, #99**.

#### المدموجة (23) — المصدر: pulls-all (state/merged_at/head/title) + pulls-files-all (الملفات)

| PR | merged_at | head.ref | العنوان | مسّ مواقع الاختبار (pulls-files-all) |
|----|-----------|----------|---------|--------------------------------------|
| #87 | 2026-11-04T15:17:49Z | fix/04-toolchain-target-and-opensuse-ovmf | Install the bare-metal target and find openSUSE OVMF | لا |
| #88 | 2026-11-04T15:17:59Z | fix/08-reject-writable-shared-mapping-of-readonly-fd | Reject writable shared mappings of descriptors not open for writing | `tests/qemu/boot.sh` +4 |
| #90 | 2026-11-04T17:39:25Z | fix/11a-overlay-open-rmdir-rename-data-loss | Stop overlay open, rmdir and rename from destroying image files | `tests/qemu/boot.sh` +5 |
| #93 | 2026-11-04T15:18:08Z | fix/01-amd-sysret-ss-rpl | Force RPL 3 in the SYSRET selector base for AMD | لا |
| #95 | 2026-11-04T15:18:15Z | fix/05-oci-utf8-space-paths | Accept UTF-8 and space characters in OCI layer paths | لا — إصلاح `crates/oci/src/lib.rs` +24/−1 |
| #97 | 2026-11-04T18:56:14Z | fix/06-relocate-efi-image-below-4g | Relocate the EFI image below 4 GiB before entering the kernel | **`tests/qemu/efi-load-above-4g.sh` ملف جديد +151** |
| #99 | 2026-11-04T15:18:24Z | fix/18-clone-thread-abi-musl-pthread | Fix the clone() thread ABI so musl pthread_create works | لا |
| #125 | 2026-11-04T18:35:52Z | fix/03-withhold-first-volume-request | Withhold the first volume request from the device until notify | لا |
| #126 | 2026-11-04T18:36:44Z | fix/02-fork-child-multi-exec-and-yield | Keep running fork children that exec twice; skip a waiting yielder | لا |
| #127 | 2026-11-04T18:37:25Z | fix/07-futex-requeue-sleep-timerfd | Match Linux futex requeue, sleep and timerfd ABI details | لا |
| #128 | 2026-11-04T18:37:58Z | fix/09-memory-syscall-arguments | Accept valid Linux arguments in runtime memory syscalls | لا |
| #130 | 2026-11-04T18:39:25Z | fix/12-posix-spawn-wait-status-sched-creds | Fix posix_spawn clone, wait status of signal deaths and wait options | لا |
| #131 | 2026-11-04T18:39:53Z | fix/13-volume-slot-header-digest-and-target | Bind slot headers into the digest and never overwrite the live slot | لا — `crates/volume-service/src/lib.rs` +130/−10 |
| #132 | 2026-11-04T18:40:21Z | fix/14-overlay-truncate-atomic-extension-timestamps | Zero truncated overlay data, keep extensions atomic, maintain times | لا |
| #134 | 2026-11-04T18:41:43Z | fix/16-overlay-merged-readdir | List overlay changes when reading image directories | لا |
| #136 | 2026-11-04T18:43:02Z | fix/19-initramfs-fallbacks-out-of-oci-domains | Keep initramfs fallbacks out of OCI domains and behind whiteouts | لا |
| #138 | 2026-11-04T18:44:15Z | fix/22a-shoot-down-cow-translations-on-all-cpus | Shoot down copy-on-write translations on all CPUs | لا |
| #140 | 2026-11-04T18:45:34Z | fix/23-chmod-image-files-symlinks | Copy image files up for chmod by path and follow symlinks | لا |
| #142 | 2026-11-04T18:46:52Z | fix/25-openat-excl-symlink-eexist | Fail O_CREAT\|O_EXCL on an existing symlink with EEXIST | لا |
| #144 | 2026-11-04T18:48:32Z | fix/27-pwrite-append-seek-data-fallocate-ftruncate | Fix pwrite O_APPEND, SEEK_DATA/HOLE, fallocate and ftruncate ABI | لا |
| **#145** | **2026-11-04T18:49:17Z** | **fix/28-volume-power-loss-tests** | **Test every volume commit against power loss at each device operation** | **`crates/volume-service/src/crash_tests.rs` جديد +305 + `crates/volume-service/src/lib.rs` +3 — اختبارات صرف** |
| #147 | 2026-11-04T18:50:55Z | fix/30-file-locks-posix-ofd-flock | Enforce POSIX, OFD and flock file locks between processes | `tests/qemu/boot.sh` +5 (+ `kernel/src/linux_file_lock.rs` جديد +410) |
| #149 | 2026-11-04T18:52:28Z | fix/32-copied-up-image-dirs-keep-entries | Keep image entries visible in copied-up image directories | لا |

#### المغلقة غير المدموجة (10) — `merged_at=null` في pulls-all

| PR | head.ref | العنوان | مسّ مواقع الاختبار |
|----|----------|---------|---------------------|
| #91 | fix/11b-overlay-symlink-stat-open-flags-preadv2 | Follow overlay symlinks in stat and fix open flag and preadv2 handling | `tests/qemu/boot.sh` +5 |
| #129 | fix/10-signal-generation-sigaction-sigaltstack | Match Linux signal generation, sigaction and sigaltstack rules | لا |
| #133 | fix/15-overlay-hard-links-nlink-eloop | Share one inode between overlay hard links and report st_nlink | `tests/qemu/boot.sh` +5 |
| #135 | fix/17-kill-only-faulting-process | Kill only the faulting process on a Linux user CPU fault | لا |
| #137 | fix/20-poll-select-sleep-run-children | Run runnable children while poll, select and sleep wait | لا |
| #139 | fix/22b-block-app-cpu-threads-in-futex-wait-and-nanosleep | Block application-CPU threads in futex wait and nanosleep | لا |
| #141 | fix/24-path-walk-enotdir-trailing-slash | Apply Linux path walk rules to file components and trailing slashes | لا |
| #143 | fix/26-renameat2-rename-exchange | Implement renameat2(RENAME_EXCHANGE) for overlay entries | `tests/qemu/boot.sh` +5 |
| #146 | fix/29-unix-socket-path-bind | Make pathname AF_UNIX binds create a socket file | لا |
| #148 | fix/31-overlay-symlinks-mid-path-relative-targets | Follow overlay symlinks mid-path and resolve relative link targets | لا |

#### خلاصة التغطية الاختبارية للمساهم الخارجي

- **مدموج (landed):** (1) **#145 = PR الاختبارات الصرفة الوحيد في الموجة**: يضيف
  `crates/volume-service/src/crash_tests.rs` (305 سطرًا جديدًا) + سطرين/ثلاثة في
  `crates/volume-service/src/lib.rs` (على الأرجح سطر `mod crash_tests;` — **غير قابل
  للتأكيد من أسماء الملفات**)، يغطي **فقدان الطاقة/power loss عند كل عملية device أثناء
  volume commit** — في crate الـvolume-service وليس volume-format. (2) **#97** يضيف
  اختبار boot صرف بصيغة shell: `tests/qemu/efi-load-above-4g.sh` (+151). (3) تعديلات
  صغيرة على هارنس `tests/qemu/boot.sh` (+4/+5) في #88، #90، #147.
  [المصدر: pulls-files-all لكل PR]
- **مفتوح (open):** **لا شيء** — كل PRs المساهم مغلقة (0 open). [pulls-all]
- **بقية الموجة (26 PR من 33)** لا تلمس أي ملف اختبار: إصلاحات ABI/overlay/sockets/locks
  في `kernel/src/**` و`crates/kernel-policy` و`services/volume` [pulls-files-all].
- ملاحظة جانبية: **#95** مدموج يصلح محلل **OCI** (قبول UTF-8 ومسافات في layer paths) —
  ليس PR اختبارات، وتعليق المشرف عليه (comments-all PR#95) يذكر `make check`/`make test`
  فقط دون ذكر اختبارات جديدة → «إضافة اختبارات: غير محدد من الـdump».

### 4d.2) أثر الموجة على crates المحللات الثلاثة (منذ 2026-11-01)

فلتر `crates/(oci|protocol-state|volume-format)/**` على pulls-files-all مع ضم pulls-all
[جميع PRs أدناه `created_at >= 2026-11-01T14:20Z`؛ لا يوجد أي PR قبل 2026-11-01 يلمس
الثلاثة في الـdump]:

| PR | المؤلف | الحالة | merged_at | ملفات المحلل (+/−) | إشارة «اختبار صرف»؟ |
|----|--------|--------|-----------|---------------------|----------------------|
| #23 | aien-spark | closed/merged | 2026-11-01T23:32:45Z | `crates/volume-format/src/lib.rs` +13/−0 | **نعم (استنتاج إشاري)** — فرع `test/volume-format-reserved-bytes` + عنوان «Test reserved volume header bytes…» |
| #32 | aien-spark | closed/merged | 2026-11-01T23:44:00Z | `crates/volume-format/src/lib.rs` +18/−0 | **نعم (استنتاج إشاري)** — فرع `test/payload-padding-independent` + عنوان «Test volume payload padding…» |
| #33 | aien-spark | closed/merged | 2026-11-01T23:45:40Z | `crates/volume-format/src/lib.rs` +25/−0 | **نعم (استنتاج إشاري)** — فرع `test/host-geometry-independent` + عنوان «Test host volume geometry validation boundaries» |
| #42 | gmkurtzer | closed/merged | 2026-11-02T02:49:30Z | `crates/oci/src/lib.rs` +47/−0 | غير محدد من الـdump (لا ملف اختبار؛ إضافة على lib.rs) |
| #44 | gmkurtzer | closed/merged | 2026-11-02T19:03:09Z | `crates/oci/src/lib.rs` +108/−71 | غير محدد من الـdump |
| #45 | gmkurtzer | closed/merged | 2026-11-02T22:04:26Z | `crates/oci/src/lib.rs` +29/−7 | غير محدد من الـdump |
| #54 | gmkurtzer | closed/merged | 2026-11-03T22:00:13Z | `crates/oci/src/lib.rs` +7/−0 | غير محدد من أسماء الملفات؛ لكن قياسنا الحي على `main@d11670e` (2026-11-04) وثّق regression `release_profile_traps_size_overflow` `#[should_panic]` في **ginux-oci** wired في `make check` [المصدر: reports/cross-check/matrix.md صف P10 — MEASURED، من دمج #54] |
| #95 | meleficarumvaldis | closed/merged | 2026-11-04T15:18:15Z | `crates/oci/src/lib.rs` +24/−1 | غير محدد من الـdump (إصلاح قبول؛ لا ملف اختبار) |

- **`crates/protocol-state`: صفر PR** في الـdump كله — لا مدموج ولا مفتوح يلمسه
  [jq `test("protocol-state|protocol_state")` على pulls-files-all = فارغ].
- **حدود الـheuristic (معلنة):** إشارات #23/#32/#33 اختبارية بالاستدلال (فرع `test/*` +
  عنوان «Test …» + ملف `lib.rs` وحيد) — كتل `#[cfg(test)]` داخل الملف غير مرئية من
  أسماء الملفات؛ أما #42/#44/#45/#54/#95 فلا دليل اختبار منها إطلاقًا إلا ما ذُكر لـ#54
  من قياس حي خارج الـdump.
- **PRنا #61 (hafid-logic، merged)** أضاف `fuzz/**` فقط (أهداف libFuzzer الثلاثة
  `fuzz/fuzz_targets/{oci,protocol,volume}_surfaces.rs` + corpora) — **لا unit tests**
  [قائمة ملفات #61 في pulls-files-all].

### 4d.3) PRs مفتوحة تضيف اختبارات صرفة (open، أي مؤلف، أي crate)

- **القائمة فارغة: 0 PR.** الـdump لا يحتوي **أي** PR بحالة `state=open` (78/78
  `closed`). [jq `group_by(.state)` على pulls-all-2026-11-05.json]
- تبعًا لذلك لا يمكن أن توجد PR مفتوحة تضيف اختبارات صرف اليوم؛ أي حكم «لا تكرار» هنا
  صالح حتى أول dump جديد فقط.

### 4d.4) PRs وكيل المشرف (gmkurtzer / فروع `codex/*`) المفتوحة

- **0 PR مفتوحة** بشرط `user == "gmkurtzer"` أو `head startswith "codex/"` مع
  `state == open` [jq على pulls-all].
- للأرقام الكلية: **gmkurtzer = 32 PR** (28 مدموجة، 4 مغلقة غير مدموجة:
  #11، #53، #101، #151)؛ **فروع `codex/*` = 6 PR** (#3، #7، #8، #9، #10، #39) كلها
  مدموجة. [pulls-all]
- حقل `changed_files` **null** في pulls-all؛ عدّ الملفات لكل PR مشتق من
  pulls-files-all عند الحاجة (مثال: #7 = 100 ملف، #39 = 80 ملفًا، #54 = 13 ملفًا).

### 4d.5) خلاصة البوابة — لكل محلل من المحللات الثلاثة

| الهدف عندنا | crate upstream | هل توجد اختبارات صرفة مدموجة/مفتوحة تغطي فجوات التغطية؟ | الدليل |
|-------------|----------------|----------------------------------------------------------|--------|
| ginux-oci | `crates/oci` | **لا** (لا PR اختبار صرف، مدموجًا أو مفتوحًا، لهذا المحلل) | الوحيد الذي لمسه منذ 2026-11-01: #42/#44/#45/#54/#95 — كلها ميزات/إصلاحات [pulls-files-all]؛ دليل اختبار الوحيد هو regression `#[should_panic]` في ginux-oci الموثق بقياسنا الحي لا بالـdump [matrix.md صف P10، MEASURED 2026-11-04 على main@d11670e]؛ إضافة اختبارات في #42/#44/#45/#95 = غير محدد من الـdump (قيد الـfilenames) |
| ginux-protocol-state | `crates/protocol-state` | **لا — ولا يوجد أي PR أصلًا** (0 مدموج، 0 مفتوح) | jq على pulls-files-all: لا سجل واحد لمسار `protocol-state` في 644 سجل الملف للـ78 PR |
| ginux-volume-format | `crates/volume-format` | **نعم جزئيًا (مدموج)**: #23/#32/#33 (aien-spark) — unit tests داخل `lib.rs` (باستدلال فرع/عنوان) تغطي reserved bytes، payload padding، host geometry | pulls-files-all: الملف الوحيد في كل منها `crates/volume-format/src/lib.rs`؛ **0 مفتوح** [pulls-all]؛ تقاطع أفكار محتمل مع بذورنا `fuzz/corpus-seed-volume/` (10-reserved-nonzero، 11-padding-nonzero، 19–23 host-header/geometry) — آليتنا fuzz لا unit، لكن أي اقتراح pure tests هنا يجب ألا يكرر الثلاثية |

- **ملاحظة على PRنا:** #61 (merged) أضاف **fuzz targets** في `fuzz/` لا unit tests
  [ملفات #61 في pulls-files-all] — لذا «تغطيتنا» آلية مختلفة ولا يلغيها ما دمجه
  aien-spark.
- **ملاحظة المجاورة:** #145 يغطي power-loss على volume commit في `crates/volume-service`
  (crate مجاور لا محلل)؛ يظل مرجعًا لنمط «اختبار صرف يقبل المشرف دمجه» [pulls-files-all
  لـ#145].
- **أثر ذلك على 4e:** مرشحو الاختبار الصرف يخرجون من فجوات لا يغطيها لا #23/#32/#33 ولا
  #145 ولا إصلاحات موجة meleficarumvaldis؛ مع وجود **صفر PR مفتوحة** اليوم فبوابة
  التكرار نظيفة حاليًا، لكنها تحتاج إعادة فحص عند أول dump جديد.

**المصادر:** inbox/upstream-dump/pulls-all-2026-11-05.json؛
inbox/upstream-dump/pulls-files-all-2026-11-05.json؛
inbox/upstream-dump/comments-all-2026-11-05.json (PR#95)؛
reports/cross-check/matrix.md (صف P10)؛ drafts/2026-11-04-next-contributions.md
(سياق #61 وخطتنا).

## 4e) المرشحون (≤5) — [MEASURED: run 41905986161 SUCCESS 5/5 على main@4d4a53bb]

> الأدلة: 37 طفرة ناجية (mutants) + تغطية 88.6% lines + 39 موضعًا حسابيًا — التفاصيل الكاملة: reports/feasibility-2026-11-05.md. لا بناء، لا فرع، لا نشر (أمر التوجيه). سياق القرار: freeze upstream — لا يُقبل PR/issues جديدة بعد 2026-11-05T07:59Z (cdf8038e)؛ النشر قرار المستخدم فقط.

| # | crate::دالة | الفجوة | دليل الفاعلية | حجم الاختبار المتوقع | بوابة التكرار (4d) | لماذا وكيل المشرف لا يغطيها | المخاطر | سؤال مسبق؟ |
|---|---|---|---|---|---|---|---|---|
| C1 | `protocol-state::checksum` (lib.rs:196,199) | قيمة ICMP checksum غير مثبتة إطلاقًا — طفرات إفساد الحساب تنجو كلها | 5 طفرات ناجية: `+=→-=`، `+=→*=`، `<<→>>`، `+→-`، `+→*` | 25–40 سطرًا: packet مع checksum محسوب سلفًا؛ قبول الصحيح ورفض الفاسد | **نظيفة تمامًا** — صفر PR لمس protocol-state في تاريخ الـ dump (78 PR) | طفرات ناجية على main مع جناحه الحالي = ادعاؤه مغطيًا كاذب؛ موجهة للإصلاحات لا تدقيق التثبيت | checksum قد تُستدعى عبر مسارات أعلى — الاختبار داخل نفس الملف `#[cfg(test)]` يتجاوز ذلك؛ 4 طفرات timeout في نفس الـ crate تلزم اختبارًا سريعًا | لا تقنيًا — النشر فقط قرارك قبل الـ cutoff |
| C2 | `protocol-state::parse_arp_reply_v4` (43–45,55,56) | تركيبات التحقق (`||`) غير مثبتة — قبول ردود ARP تفشل بشرط واحد | 5 طمرات ناجية `||→&&` (شرط يصير أصرم ولا شيء يفشل) | 30 سطرًا: table-driven، رفض رد يخالف حقلًا واحدًا لكل حالة | نظيفة تمامًا (كما C1) | نفس دليل C1 | قد تتقاطع جزئيًا مع بذورنا `corpus-seed-protocol/p03–p09` (fuzz لا unit — تكامل لا تكرار) | لا تقنيًا |
| C3 | `volume-format::HostVolumeHeader::decode` (69–72, 82:29) | شروط قبول الترويسة غير مثبتة كتركيبات | 5 طمرات ناجية `||→&&` ×4 و`&&→||` ×1 **فوق** اختبارات #23/#32/#33 المدموجة | 40 سطرًا: ترويسة تخالف قيدًا واحدًا لكل حالة | **جزئية** — #23/#32/#33 (aien-spark، مدموجة) تختبر reserved/padding/geometry، لكن بقاء الطمرات يثبت أن تركيبات هذه الأسطر خارج تغطيتها؛ يجب ألا يكرر المرشح حالاتها الثلاث المسماة | بقاء الطمرات فوق دمجها هو الدليل الحاسم | التداخل مع حالات #23/#32/#33 إن لم تُبنَ حالات على «قيد واحد مخالف» حصرًا | لا تقنيًا — يُذكر الفرق عن الثلاثية صراحة في أي نص |
| C4 | `volume-format::decode` (125–127, 138:9) | نفس النمط في تحقق الهندسة/حجم القطاع أسفل الترويسة | 4 طمرات ناجية `||→&&` | 30 سطرًا، table-driven | جزئية (كما C3) — نفس الاحتياط | نفس الدليل | نفس خطر C3؛ دمجه مع C3 في PR واحد يخفض الكلفة | لا تقنيًا |
| C5 | `oci` — مسارات رفض المحلل (82.2% lines، 118 FNDA=0 غير عامة، 29 موضعًا حسابيًا) | أدنى تغطية بين المحللات؛ مسارات الخطأ غير مختبَرة | تغطية قياسية (لا طفرات — oci خارج ميزانية 20 دقيقة للطفرات)؛ نمط «تثبيت ناقص» مثبت في الشقيقيين C1–C4 | 60–120 سطرًا — يحتاج تمريرة تحديد أولاً | لا PR اختبار صرف على oci (فقط إصلاحات #42/#44/#45/#54/#95) | إصلاحاته المدموجة لا تضيف تدقيقًا للرفض؛ الجناح يترك 165 سطرًا غير مغطاة | النطاق أوسع من «تغيير واحد + اختبار واحد»؛ اختيار المسارات اعتباطي بلا سؤال | **نعم** — سؤال تخصيص (أي مسارات أولًا) + قرار النشر |

- **احتياطي خارج الخمسة:** `kernel-policy::valid_vtd_write_fault_record` (8 طمرات `<<→>>`، `|→^`، `&→|/^`) + `merged_directory_next:76` — أصغر crate (85 LOC، تغطية 98.7%) وأسهل تثبيت؛ مؤجل لعدم كونه محللًا.
- **ترتيب التوصية:** C1 > C2 > C3+C4 (PR واحد) > C5. كل C1–C4 على نمط مسبوق بقَبول upstream لاختبارات صرف (#145 power-loss tests، #23/#32/#33) — لكن النافذة تُغلق 2026-11-05T07:59Z وبعدها تُغلق أي فتح دون مراجعة.

**المصادر:** run [41905986161](https://github.com/hafid-logic/ginux-watch/actions/runs/41905986161) (artifacts + step logs)؛ reports/feasibility-2026-11-05.md؛ القسم 4d أعلاه (dump 2026-11-05)؛ README@cdf8038e (freeze).

## تحديث v3.4 (2026-11-05، جلسة 26) — C1+C2 خرجا من الترشيح إلى البناء

- **بوابة الاستبعاد (§3 التوجيه): KEEP** [MEASURED — team/results/T-20261105-02/result.md]: 78 PR في الـdump لا يلمس protocol-state؛ 0 PR/issues مفتوحة حيًا؛ آخر commit على ملف الكرين 2026-10-13 (قبل قاعدتنا)؛ و10 طفرات ناجية للدالتين على main@4d4a53bb (run 41905986161) تثبت عدم وجود تغطية. errata مسجل: حكم W2 الأول «DROP» كان ملوثًا بالذات (قرأ فرعنا المحلي ظنًا أنه main) وصُحح بواسطة المشرف إلى KEEP.
- **C1+C2 → سلّم: branch** [MEASURED]: فرع `feature/tests-protocol-state` = `2b4e119e117d85294cc6da0f5c60727b68f359b6` في hafid-logic/ginux (من upstream main@4d4a53bb؛ fork main مُزامن ff من c86945b1)؛ +62 سطرًا في `crates/protocol-state/src/lib.rs` فقط (اختبارات صرفة؛ 4 #[test] + helper؛ commit "Test protocol-state checksum and ARP checks" بتوقيع -s وهوية noreply).
- الإثبات الديناميكي (mutants قبل/بعد + make check/test على 10.0.13 و10.1.2): runs 41915470999 (pr-a-mutants) و41915447820 (builder-verify) — نتائجهما في reports/2026-11-05.md §2. الهدف: 0 ناجية للدالتين بعد (قبلها: 5+5 ناجية).
- status: C1/C2 = branch → draft-PR (داخل fork فقط)؛ النشر إلى upstream = قرار المستخدم قبل cutoff 2026-11-05T07:59Z.

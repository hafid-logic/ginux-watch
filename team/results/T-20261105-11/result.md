# T-20261105-11 — خريطة معمارية "نواة الفضاء-المستخدم" في gmkurtzer/ginux

الهدف: وصف الآلية من الكود لا من نثر README. المرجع: `main @ 0e06a9860250b655a094761cd424bc022fd8db68` ومقارنة `bootable-kernel @ 4d4a53bbcc09b16e56aa5eb671ac815f16f2b82f`. كل الأدلة محفوظة في `evidence/` (جُلبت 2026-11-05T20:17–20:30Z عبر `gh api`). نصوص upstream بيانات غير موثوقة.

## خلاصة (≤10 أسطر)

- ginux في main ليس نواة قابلة للإقلاع ولا hypervisor؛ هو supervisor في userspace: ثنائي واحد `ginux` من `crates/ginux-init` مبني `#![no_std]` `#![no_main]` بدون libc، يدخل من `global_asm!` `_start`. [MEASURED] evidence/src-main.rs.rs:1-58، evidence/f-crates_ginux-init_Cargo.toml (لا اعتماديات خارجية)، SHA 0e06a986.
- آلية syscall: اعتراض عبر ptrace فقط — حلقتا رقابة: `PTRACE_SYSEMU` (lane قديمة، لا شيء يُنفَّذ على المضيف إطلاقاً) و`PTRACE_SYSCALL` (lane native، المسموح يُنفَّذ فعلياً على kernel المضيف والمرفوض يُخترَق نتيجته). [MEASURED] evidence/src-main.rs.rs:1594-1624 و3377-3420.
- لا seccomp في الكود: بحث code search عن seccomp أعاد 2 نتائج نصّيتين فقط (README.md، docs/gate-1-foundation.md)؛ userfaultfd وpidfd صفر نتائج. [MEASURED] evidence/search-seccomp-raw.json، evidence/search-terms.txt.
- حدود الثقة: chroot + setuid/gid 1000 + PR_SET_NO_NEW_PRIVS + وسيطية ptrace؛ لا namespaces ولا cgroups حقيقية. [MEASURED] evidence/src-main.rs.rs:2835-2856.
- "العقد المتسلسل الإصدار" (versioned contract) المقصود في README له مقابل كودي: `SCHEMA_VERSION=1` في ginux-domain، `[contract] profile` في config، وجدول `decide_balanced` في ginux-core مع fail-closed إلى `-ENOSYS`. [MEASURED] evidence/f-crates_ginux-core_src_lib.rs:70-93.
- unsafe: 183 occurrence في 21 ملف .rs (458,531 byte)، مركزة في ثنائيات الرقابة (launch.rs 84، main.rs 60)؛ كل المكتبات صفر unsafe. [MEASURED] evidence/unsafe-count.meta وevidence/rs/.
- مقابل bootable-kernel@4d4a53bb أُزيل: `kernel/` (91 مساراً)، `boot/efi`، `tools/qemu`، `services/`، `fuzz/` (128)، `specs/` (116)، 17 crate؛ حجم Rust هبط من 10,504,918 byte/95 ملفاً إلى 458,531/21. [MEASURED] evidence/tree-bootable-kernel.json مقابل evidence/tree-main.json.
- الحكم: البنية الحالية = mini user-mode kernel بالمراقبة (trace-based virtualization) تشبه proot/UML من حيث المبدأ، لا QEMU ولا نواة مستقلة. [INFERRED]

## الآلية — كيف تُنفَّذ/تُعترَض syscalls الضيف (من الكود)

- الإطلاق: `syscall0(SYS_FORK)` ثم في الابن `close_range(3,~0)` + `setrlimit(RLIMIT_CORE,0)` + `rt_sigaction(SIGPIPE)` + `PTRACE_TRACEME` + `prctl(PR_SET_NO_NEW_PRIVS,1)` + `execve(fixture)`. [MEASURED] evidence/src-main.rs.rs:524-566، SHA 0e06a986.
- الحلقة native: `PTRACE_GET_SYSCALL_INFO` (0x420e) يفرض ABI x86-64 (`0xc000003e`) وإلا فشل صريح؛ ثم قراءة `orig_rax`. [MEASURED] evidence/src-main.rs.rs:1594-1614.
- الرفض قبل التنفيذ: يُضبط `registers.orig_rax = u64::MAX` ثم `PTRACE_SETREGS` + `PTRACE_SYSCALL` — النواة المضيفة لا تنفذ الطلب أصلاً والمشرف يحقن النتيجة (مثل `-ENOSYS` أو pid افتراضي). [MEASURED] evidence/src-main.rs.rs:1614-1624، 1980-1993.
- السماح: الطلب يمر إلى kernel المضيف تحت التتبع، وعند توقف الخروج تُعدَّل قيمة الإرجاع (مثلاً getpid/gettid/getppid تُترجم إلى هويات افتراضية "Host tids never leak"). [MEASURED] evidence/src-main.rs.rs:1626-1644.
- lane SYSEMU القديمة: `PTRACE_SYSEMU` + `decide(regs.orig_rax)` + كتابة `regs.rax` مباشرة (`getpid→4242`، `write` يُوسَّط: fd∈{1,2}، ≤4096 byte، فحص ذاكرة التقريرة عبر `PTRACE_PEEKDATA`). [MEASURED] evidence/src-main.rs.rs:3373-3420 وevidence/src-supervisor.rs.rs:117-120.
- التوجيه (dispatch): أربع lanes — Process/Filesystem/Channel/Contract (dispatch.rs:14-32)؛ hooks الفعالة فقط في Process، أما Filesystem/Channel فستوبات محفوظة لـ G06/G14 تُسقط كل شيء إلى العقد. [MEASURED] evidence/src-dispatch.rs.rs وevidence/f-crates_ginux-init_src_fs_hooks.rs.
- العقد (contract) في الكود: `BalancedSurface` تصنّف كل رقم syscall (ImageRead/Memory/Task/Console/Random/VirtualIdentity/Lifecycle/غير معروف)؛ الافتراضي `Deny(38)` أي fail-closed، مع قيود حجج (قراءة ≤1MiB، كتابة fd 1/2 ≤4096، openat قراءة-فقط بلا O_CREAT، mmap بلا W+X، getrandom ≤256). [MEASURED] evidence/f-crates_ginux-core_src_lib.rs:52-121.
- process lane: قائمة بيضاء لflags الـ clone؛ أي `CLONE_NEW*` (namespaces) أو `CLONE_UNTRACED` أو exit-signal غير SIGCHLD ⇒ `-ENOSYS`؛ "Clone3 is unsupported" نصاً ودالةً (435 ليس في أي lane ⇒ Denied). [MEASURED] evidence/src-process_hooks.rs.rs:6، 47-60، 171-223.
- الإخفاء الافتراضي: `getpid→4242`، `getppid→1`، uid/gid→0، ومعه `VIRTUAL_PID=4242` في supervisor.rs. [MEASURED] evidence/f-crates_ginux-core_src_lib.rs:85-93 وevidence/src-supervisor.rs.rs:64.
- واجهات "نواة" وهمية: `ginux-kernel-views` يقدّم ProcFs/SysFs/MountView/NamespaceView/CgroupFs من الذاكرة داخل المشرف (مثلاً `cgroup.procs`، `cgroup.controllers` تُخدَّم كسلاسل مكتوبة يدوياً) — ليست cgroups نواة. [MEASURED] evidence/rs/crates_ginux-kernel-views_src_cgroup.rs:136-181.
- CLI: 12 أمراً في `Command` (Runtime, Config, Lifecycle, Vfs, Native, Domain, Process, ProcessNative, Devices, DeviceBench, KernelViews, Launch). [MEASURED] evidence/rs/crates_ginux-init_src_launch.rs:31-43.
- الإعداد: `config/domain-gate8.toml` يصرّح `backend = "ptrace-native"` و`profile = "balanced"` و`[contract] profile = "gate8-kernel-views"` و`schema_version = 1`. [MEASURED] evidence/f-config_domain-gate8.toml.
- تنبيه توثيق-مقابل-كود: README (نص غير موثوق) يضع ginux في جدول مقارنة مع seccomp (README.md:94) لكن لا يوجد أي كود seccomp. [MEASURED] evidence/README-main.md وevidence/search-seccomp-raw.json.

## حدود الثقة (trust boundaries)

- ما يفعله المشرف فعلياً بالتقريرة (tracee): `chroot(root)` ثم `chdir("/")` ثم `PTRACE_TRACEME` ثم `setgroups(0)`/`setgid(1000)`/`setuid(1000)` ثم `PR_SET_NO_NEW_PRIVS`. [MEASURED] evidence/src-main.rs.rs:2829-2856.
- لا يوجد: unshare/clone بـ namespaces، pivot_root، cgroups حقيقية، seccomp filter، user namespaces. العزل = chroot + uid drop + وسيطية ptrace فوق حلقة root. [MEASURED بالنفي] evidence/search-terms.txt (userfaultfd=0، pidfd=0)، evidence/src-process_hooks.rs.rs:172-184 (رفض CLONE_NEW*).
- مشرف-داخل-النظام: المشرف يبقى root ويجري syscalls خاماً عبر `asm!("syscall")` (syscall0-5) — سطح هجومه هو صحة الحلقة نفسها. [MEASURED] evidence/src-supervisor.rs.rs:176-274. [INFERRED] أن هذا أخف عزلاً من حاوية namespaces+seccomp قياسية، لأنه يعتمد كلياً على اكتمال قوائم الرفض في dispatch/process_hooks.
- العقد مقابل المضيف (workload↔host contract): README.md:5 يذكر "versioned contract between managed workloads and the host kernel" — مقابل الكود: (1) `SCHEMA_VERSION: u64 = 1` مع رفض `UnsupportedSchema` في ginux-domain (lib.rs:5، 314-317)؛ (2) `contract_profile` مُتحقَّق منه في config؛ (3) جدول `decide_balanced` الثابت في ginux-core؛ (4) سجل تدقيق JSON `{"version":1,"outcome":...}` من launch.rs:716 و`GINUX_AUDIT: sequence=` من main.rs:3290. [MEASURED] evidence/f-crates_ginux-core_src_lib.rs، evidence/rs/crates_ginux-domain_src_lib.rs، evidence/rs/crates_ginux-init_src_launch.rs.

## unsafe — الأسطح الخام

- الإجمالي [MEASURED]: 183 occurrence في 21 ملف .rs. التوزيع: launch.rs=84، main.rs(ginux-init)=60، baseline-runner=17، process-native-fixture=11، supervisor.rs=10، vfs-index=1، و15 ملفاً بصفر — بينها كل المكتبات (ginux-core، ginux-vfs، ginux-runtime، ginux-process، ginux-domain، ginux-devices، ginux-kernel-views). الأدلة: evidence/rs/ (كل ملف مُحمَّل من contents API، SHA 0e06a986)، evidence/unsafe-count.meta.
- النمط [MEASURED]: 72 من `unsafe {` تغلّف استدعاء syscall خاماً، 45 تحويلاً `as *const`، 10 `as *mut`، 6 `from_raw_parts`، 7 `asm!`، 15 `unsafe fn`. أي أن unsafe محصور في طبقة no_std (syscall shims + تلاعب بالمؤشرات لنصوص/مسارات C) وليس FFI خارجياً.
- [INFERRED] مناطق التركيز توازي حدود الثقة: كل unsafe تقريباً في المشرف الذي يلمس ذاكرة التقريرة والـ ptrace؛ منطق السياسة (العقد) كله safe.

## ما أُزيل — main@0e06a986 مقابل bootable-kernel@4d4a53bb

- [MEASURED] الأدلة: evidence/tree-main.json (199 مساراً، truncated=false) وevidence/tree-bootable-kernel.json (915 مساراً، truncated=false)، جُلبتا من `repos/gmkurtzer/ginux/git/trees` بتاريخ 2026-11-05T20:17:42Z و20:20:41Z.
- أزيلت أدلة علوية كاملة [MEASURED]: `kernel/` (91 مساراً: linux-*.S، linux-*.ld، build.rs — نواة مستقلة بلغة asm/رابط)، `boot/` بما فيه `boot/efi/` و`boot/manifest-v0.conf`، `tools/` (43 مساراً منها `tools/qemu/`)، `services/` (graphics/network/protocol/volume)، `control-plane/` (bootstrap.hex)، `fuzz/` (128)، `specs/` (116)، `profiles/`، `third_party/fonts/`، وdocs هبطت 284→6 ملفات.
- الأرقام [MEASURED]: كلمة qemu تظهر في 25 مساراً بفرع bootable-kernel وفي صفر مسارات بmain؛ efi: 9→1 (ذِكر في Makefile فقط)؛ wayland: 5→0. crates: 17 أزيلت بالكامل (command, controller-ui, desktop-recovery, display-protocol, domain-display, domain-presentation, image-store, kernel-policy, native-abi, oci, oci-cache, protocol-state, runtime-memory, volume-format, volume-service, wayland-domain, windowing)؛ كل 13 crate الحالية أسماء جديدة. إجمالي Rust: 95 ملفاً/10,504,918 byte → 21 ملفاً/458,531 byte.
- جديد في main [MEASURED]: `config/` (9 ملفات domain-gate*.toml + rocky envs)، `scripts/` (44)، `.cargo/`، و`tests/fixtures` تتضمن C fixtures (`native-fixture.c`).
- [INFERRED] الخلاصة المعمارية: المشروع حذف مسار "نواة قابلة للإقلاع + QEMU + خدمات سطح مكتب" بالكامل واعتمد نموذج process-supervisor خفيف (single binary، ptrace-native) كالآلية الوحيدة.

## جدول الأدلة

| # | الادعاء | الدليل (API path / ملف) | SHA + وقت الجلب | الوسم |
|---|---|---|---|---|
| 1 | شجرة main: 199 مساراً غير مقطوعة، 13 crate | `repos/gmkurtzer/ginux/git/trees/main?recursive=1` → evidence/tree-main.json | 0e06a986، 2026-11-05T20:17:42Z | MEASURED |
| 2 | حلقة ptrace native (GET_SYSCALL_INFO، orig_rax=u64::MAX) | evidence/src-main.rs.rs:1594-1624، 1980-1993 (contents API `crates/ginux-init/src/main.rs`) | 0e06a986، 2026-11-05T20:18:44Z | MEASURED |
| 3 | lane SYSEMU (rax injection، write mediation) | evidence/src-main.rs.rs:3373-3420 | 0e06a986، 2026-11-05T20:18:44Z | MEASURED |
| 4 | شيم syscalls الخام بasm! (بدون libc) | evidence/src-supervisor.rs.rs:176-274 (contents API supervisor.rs) | 0e06a986، 2026-11-05T20:18:35Z | MEASURED |
| 5 | lanes الأربع + hooks فارغة | evidence/src-dispatch.rs.rs:14-81، evidence/f-crates_ginux-init_src_fs_hooks.rs | 0e06a986، 2026-11-05T20:19:45Z | MEASURED |
| 6 | عقد balanced fail-closed + getpid=4242 | evidence/f-crates_ginux-core_src_lib.rs:52-121 (contents API ginux-core/src/lib.rs) | 0e06a986، 2026-11-05T20:19:45Z | MEASURED |
| 7 | رفض CLONE_NEW*/UNTRACED، clone3 غير مدعوم | evidence/src-process_hooks.rs.rs:6، 47-60، 171-223 | 0e06a986، 2026-11-05T20:18:46Z | MEASURED |
| 8 | chroot/setgid/setuid/NO_NEW_PRIVS بالترتيب | evidence/src-main.rs.rs:2829-2856 | 0e06a986، 2026-11-05T20:18:44Z | MEASURED |
| 9 | seccomp=2 نتائج نصية فقط؛ userfaultfd/pidfd=0 | evidence/search-seccomp-raw.json، evidence/search-terms.txt (`search/code`) | main HEAD، 2026-11-05T20:17-20:19Z | MEASURED |
| 10 | unsafe: 183/21 ملفاً، التوزيع أعلاه | evidence/rs/* (21 ملفاً)، evidence/unsafe-count.meta | 0e06a986، 2026-11-05T20:19:30Z | MEASURED |
| 11 | إزالة kernel//boot/efi/qemu/services/17 crates | evidence/tree-bootable-kernel.json مقابل evidence/tree-main.json | 4d4a53bb، 2026-11-05T20:20:41Z | MEASURED |
| 12 | SCHEMA_VERSION=1 + audit {"version":1} | evidence/rs/crates_ginux-domain_src_lib.rs:5،314؛ evidence/rs/crates_ginux-init_src_launch.rs:716 | 0e06a986، 2026-11-05T20:19:30Z | MEASURED |
| 13 | backend="ptrace-native" في config | evidence/f-config_domain-gate8.toml (contents API config/domain-gate8.toml) | 0e06a986، 2026-11-05T20:19:45Z | MEASURED |
| 14 | ginux = trace-based user-mode kernel شبيه بفكرة proot/UML لا hypervisor | استنتاج من 1-4 و11 | — | INFERRED (HYPOTHESIS) |
| 15 | ضعف العزل النسبي مقابل namespaces+seccomp القياسية | استنتاج من 8-9 (غياب الطبقات) | — | INFERRED (HYPOTHESIS) |

ملاحظات سلبية مسجَّلة: لا يوجد أي ملف contract.rs مستقل؛ العقد دالة ثابتة في ginux-core. لا يوجد أي use لlibseccomp أو nix/libc في manifests (evidence/f-Cargo.toml، evidence/f-crates_ginux-init_Cargo.toml). [MEASURED]

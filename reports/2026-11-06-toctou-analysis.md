# تحليل TOCTOU القرائي — مسارات ptrace/SYSEMU في ginux @ `64a3e3f7` (توجيه v5.1 بند 9، 2026-11-06)

- **الوضع:** قراءة وتحليل فقط — لا كود، لا فرع، لا PR (بوابة v5.1-3: القراءة والتحليل غير مشمولين بقيود التداخل). يحل خيار (ب) من drafts/2026-11-06-toctou-candidate-hold.md.
- **الترسيخ [MEASURED]:** الشجرة محللة عند commit `64a3e3f7` (نسخة `/work/ginux-pin`، checkout مُتحقق بـrev-parse)؛ `ls-remote` عند 04:5xZ يؤكد أن upstream/main ما زال `64a3e3f7`.
- **الوسم:** MEASURED = قراءة مباشرة للشجرة المثبتة (ملف:سطر) أو قياس حي؛ INFERRED = استنتاج سلوك السباق/التزامن من الكود دون تنفيذ.

## 1) المسارات الأربعة [MEASURED]

| المسار | الملف | الآلية | الاستخدام |
|---|---|---|---|
| حلقة الإطلاق | `crates/ginux-init/src/launch.rs:877–1078` (`supervise_launch`) | PTRACE_SYSCALL + PTRACE_GET_SYSCALL_INFO@966–978، القرار `decide_native`@981 | إطلاق النطاق (مرحلة الإقلاع) |
| حلقة process-native | `crates/ginux-init/src/main.rs:592–2057` (`supervise_process_native`؛ التابع helpers حتى ~2452) | PTRACE_SYSCALL@662/1022… + GET_SYSCALL_INFO@1624–1643 + أحداث TRACEFORK/TRACECLONE/TRACEVFORK/TRACEEXEC | الإشراف العملي متعدد المهام |
| الحلقة native الأحادية | `crates/ginux-init/src/main.rs:3038–3216` (`supervise_native`؛ يليها `native_fail`@3218) | PTRACE_SYSCALL + GET_SYSCALL_INFO@3100–3112، `decide_native`@3115 | وضع المهمة الواحدة |
| gate1 (SYSEMU قديمة) | `crates/ginux-init/src/main.rs:3394–3618` (`gate1_main`) | PTRACE_SYSEMU@3537/3615 — توقف دخول فقط، النتيجة تُكتب rax مباشرة + SETREGS@3612 | fixture اختباري ذاتي (GATE1: PASS@3597)، ليس مسار إنتاج |

آلية التنفيذ/التخطي [MEASURED]: emulate = `orig_rax = u64::MAX` + SETREGS (تخطي النواة؛ النتيجة تُحقن عند توقف الخروج أو مباشرة في SYSEMU) — launch.rs:995–1004/1018–1026، main.rs:1654/1674/3129–3138/3152–3160؛ passthrough = استئناف PTRACE_SYSCALL دون تغيير orig_rax — launch.rs:1045–1047، main.rs:3173+؛ deny = تخطٍّ مع rax=-errno — launch.rs:1051–1073.

## 2) مدخلات القرار سجلية حصرًا — لا موقع واحد يقرأ ذاكرة الـtracee ليقرر [MEASURED]

- العقد الكامل: `crates/ginux-core/src/lib.rs` — `decide`@32–40، `balanced_surface`@54–70، `decide_balanced`@72–85، **`balanced_arguments_allowed`@125–152 (سجلات فقط: أعداد/أعلام/bits — صفر قراءة ذاكرة)**.
- التوجيه: `crates/ginux-init/src/dispatch.rs:22–32` (تصنيف Lanes)، `:48–81` (`decide_native`، ومنع fork@51–56)، `:89–91` (تمرير سجلات).
- خطاف process: `crates/ginux-init/src/process_hooks.rs` — `claim`@ (فحص flags في rdi فقط)، `thread_supported`@ (flags فقط)، `exec_mediated`@ (dirfd/flags فقط). خطافا fs/channel فارغان (fs_hooks.rs:8–18، channel_hooks.rs:8–19 — G06/G14 لاحقان).
- أذرع الحلقة process-native سجلية باستثناء واحد معلن: الهوية@1657–1675، clone flags@1676–1705، futex-PI `rsi&0x7f`@1708–1716، get_robust_list pid@1717–1726، exec `dirfd/flags`@1732–1745، wait4 `selector/options`@1746–1760، بوابة read على `rdi`@1951–1962، بوابة write@1964–1990. **الاستثناء:** فرع wait4 المحجوز يستعلم `termination_pending`@2113–2161 بحالتين kernel-state (`PTRACE_GETSIGMASK`@2125 + `PTRACE_PEEKSIGINFO`@2143 — حالة نواة لا ذاكرة مستخدم) ليختار بين park وإعادة البدء@1815 — **كلا الفرعين يبقيان `orig_rax=u64::MAX` (لا passthrough)**@1820/1836، فلا يؤثر على خلاصة §5 [MEASURED].

## 3) الجدول — لكل syscall: مصيره ووسائطه المؤشرية [MEASURED ما لم يُوسم]

**Emulate (تخطي النواة؛ لا وسائط مؤشرية أصلًا):** الهوية الافتراضية 39/102/104/107/108/110/111 (lib.rs:65–66؛ النتيجة من ProcessTable في process loop@1657–1675 أو ثابتة 4242 في launch/[personal-email-redacted]:1013–1026/main.rs:3147–3160)؛ Lifecycle 60/231 (domain-stop — launch.rs:1028–1034، main.rs:3162–3172). ⇒ لا مجال لـTOCTOU.

**Deny(38) fail-closed (لا تنفيذ إطلاقًا):** كل ما ليس له surface (lib.rs:68/81) + fork في dispatch.rs:51–56 + فشل فحص الوسائط السجلي (launch.rs:1049–1059).

**Mediate/passthrough (النواة تنفذ؛ مَن يفحص المؤشرات؟ النواة وحدها، ذريًا داخل النداء — ginux لا يقرأ الذاكرة ولا ينسخ منها للقرار):**
- ImageRead: 0 (read، buf=rsi)؛ 2/257 (open/openat، path)؛ 3 (close)؛ 4/5/262/332 (stat العائلة)؛ 8 (lseek)؛ 17 (pread64)؛ 21/439 (access/faccessat2)؛ 72 (fcntl)؛ 89 (readlink)؛ 217 (getdents64) — فحص ginux سجلي فقط (lib.rs:139/142/144/145 وlaunch/native تمرر الأصل للنواة؛ process loop: read gated بالـfd@1951–1962).
- Memory: 9/10/11/12/28 (mmap/mprotect/munmap/brk/madvise) — فحص prot bits سجلي (lib.rs:143).
- Task: 13/14/15 (الإشارات — النواة تنسخ sigmask ذريًا)؛ 56 (clone — أدناه)؛ 57/58 (fork/vfork — أحداث تعقب)؛ 61 (wait4 — **مُحاكى كليًا**، أدناه)؛ 99/302 (rlimits)؛ 158 (arch_prctl)؛ 202 (futex — منع PI سجليًا@1708–1716؛ uaddr تديره النواة ذريًا)؛ 218 (set_tid_address — passthrough + ترجمة rax عند الخروج)؛ 273/334 (set_robust_list/rseq — passthrough صرف@1707)؛ 274 (get_robust_list — rewrite rdi→0@1717–1726).
- Console: 1/20 (write/writev — فحص fd/حدود سجلي lib.rs:140–141 + بوابة المرآة@1964–1990؛ محتوى buf لا يقرأه ginux إطلاقًا).
- Random: 318 (getrandom — النواة تملأ buf).
- process lane إضافي: 22/293 (pipe/pipe2 — flags سجليًا؛ passthrough؛ **قراءة ما بعد التنفيذ للمرآة**، أدناه)؛ 32/33/292 (dup/dup2/dup3)؛ 62 (kill — rewrite rdi افتراضي→مضيف عند الدخول@1944–1945 مع حفظ الأصل للترجمة العكسية@1568–1570، النواة تتحقق)؛ 59/322 (execve/execveat — `exec_mediated` سجليًا؛ path/argv/envp تقرأها النواة وحدها ذريًا).

## 4) جرد مواضع لمس فضاء عناوين الـtracee — ثمانية [MEASURED]

**مواضع بيانات المستخدم (خمسة):**

1. `read_tracee_word` — supervisor.rs:117–120 (PEEKDATA، كلمة واحدة، bool) — **تُستدعى في موقع واحد: main.rs:3578 داخل gate1 فقط**.
2. `read_tracee_pipefds` — main.rs:2370–2394 (PEEKTEXT بايت-بايت) — تُستدعى @1325 **بعد** تنفيذ النواة لpipe/pipe2 بنجاح؛ قراءة نتيجة (تعويض مرآة PipeSpace) لا قرار passthrough؛ فشل ⇒ `killed_or_fail`@1355 (fail-closed).
3. `store_tracee_status` — main.rs:2400–2423 (PEEK+POKEMERGE لحفظ بايتات الجوار) — wait4 فوري@1770 ومستيقظ@2315–2317؛ فشل ⇒ killed_or_fail@1773/2321–2323.
4. `zero_tracee_rusage` — main.rs:2429–2443 — wait4@1783/2327–2329؛ نفس معالجة الفشل.
5. `store_tracee_tid` — main.rs:2450–2452 — نشر الـtid الافتراضي في خلايا clone ptid/ctid@1505–1522 و@1155–1156/1202 (المؤشران ملتقطان من rdx/r10@1687–1700 أثناء توقف الدخول).

**مواضع ترقيع نص break-point (ثلاثة — فضاء العناوين، ذاكرة الأب النصية):**

6. PEEKTEXT لقراءة كلمة نص الأب — main.rs:963–968 — الكلمة تُخزن للاستعادة فقط (`fork_breakpoint_word`@1000، استعادة@1128) ولا تدخل قرارًا؛ فشل ⇒ fail-closed@970.
7. POKETEXT لتثبيت 0xCC — main.rs:979–984 — فشل ⇒ fail-closed@986.
8. POKETEXT لاستعادة الكلمة — main.rs:1124–1129 — فشل ⇒ fail-closed@1131.

وكشف تكاملي: `PTRACE_GETSIGINFO`@launch.rs:909–913 — probe حالة نواة (نجاح/فشل يوجّه تمرير الإشارة، لا محتوى) [MEASURED].

## 5) جواب السؤال المحوري: هل تُنسخ الوسائط المؤشرية قبل الفحص؟

**لا يوجد نمط «فحص-ذاكري ثم تمرير المؤشر الأصلي» في أي مسار** [MEASURED]. ثلاث حالات:
- passthrough: ginux لا يفحص الذاكرة أصلًا — الفاحص الوحيد هو النواة داخل النداء (ذري).
- emulate: القرارات كلها من السجلات (§2)؛ لا مستهلك لبيانات المؤشرات إلا كتابات wait4/clone (§4-3/4/5) وهي كتابات نتيجة لا فحوص مدخلات.
- gate1 write@3573–3584: فحص كلمة واحدة (3578) ثم **rax=rdx دون تنفيذ النواة** («host-write=not-executed»@3583) — لا أحد يستهلك الـbuffer بعد الفحص ⇒ نافذة TOCTOU هنا عديمة الأثر (فقط تقلب بين deny ونجاح مؤلَّف) [MEASURED].

## 6) حسم الفرضية «المحاكاة لا تتأثر» والمخاطر المتبقية

- **على مستوى القرارات: الفرضية صحيحة** [MEASURED بالقراءة — §2/§5].
- **بقايا سباق (كلها INFERRED، وكلها داخل ذاكرة الـtracee، ولا واحدة تعبر حدود الصندوق):**
  - (أ) نافذة «التقاط-ثم-كتابة» في wait4 (status@1753→1770/2316، rusage@1755→1783/2328) وclone (ptid/ctid@1687–1700→1505–1522): النداء موقوف ptrace أثناء الكتابة لكن **الخيوط الشقيقة تُبقى جارية** (CLONE_THREAD مدعوم — process_hooks `thread_supported` + main.rs:1683–1684)؛ شقيق يلغي/mmap الصفحة بين الالتقاط والكتابة ⇒ poke يفشل (EIO) ⇒ fail-closed (killed_or_fail/mark_killed) في `64a3e3f7`. **انتبه: #221 المفتوحة تغيّر هذه السياسة تحديدًا** (§8).
  - (ب) نافذة PEEK→POKE غير الذرية في store_tracee_status/store_tracee_tid: تغيّر شقيق بايتات الجارة بين القراءة والدمج ⇒ إعادة كتابة بايتات قديمة («بدون لمس الجوار»@2365–2368 ينكسر تحت تزامن) — تلف داخل-الـtracee فقط.
  - (ج) read_tracee_pipefds@2370 قد تقرأ مصفوفة عبث بها شقيق بعد كتابة النواة ⇒ مرآة مضللة داخلية (المهاجم يكذب على محاسبة fds الخاصة به وحده).
  - (د) نافذة breakpoint على نص الأب: تثبيت 0xCC@980 ثم الاستعادة@1125 عبر توقفَي حدث fork — نص أب متعدد الخيوط عند rip التطابق يصطاد SIGTRAP غريبًا؛ الأثر داخل فضاء الـtracee والفشل fail-closed@970/986/1131 [INFERRED].

## 7) تصميم اختبار متعدد الخيوط (نص فقط — لا كود) ومعيار الفشل

- **T1 (نافذة أ):** مهمة بخيطين: خيط A يستدعي wait4 منتظرًا على ابنٍ منجز (status_ptr في صفحة قابلة للفك)؛ خيط B يكرر: munmap للصفحة ثم mmap PROT_NONE بنفس العنوان؛ نُقيس ما يحدث عند الاستيقاظ. **معيار النجاح (fail-closed):** wait4 يُنهى بخطأ (بعد #221: -EFAULT) أو يُقتل الإشراف (`killed_or_fail`) — لا نجاح صامت. **معيار الفشل:** wait4 يعيد نجاحًا بكلمة status قديمة/عشوائية، أو يستمر الإشراف صامتًا بعد poke إلى صفحة PROT_NONE.
- **T2 (نافذة ب):** كاتب شقيق دائم على الـint المجاور لكلمة status؛ يُفحص التمزق (قيمة مجاورة ترجع لقيمة قديمة). الفشل = رصد ارتجاج قيمة كتبها الشقيق بعد PEEK وقبل POKE.
- **T3 (نافذة ج):** شقيق يعيد كتابة مصفوفة pipefd بعد النواة؛ يُفحص audit سطر pipe مقابل الأزواج الحقيقية (المعيار: عدم قبول المرآة أزواجًا لم تصدر عن النواة — اليوم تقبلها [MEASURED@1323–1353] ⇒ فجوة محاسبية داخلية معلومة).
- لا يُنفَّذ أي منها كودًا الآن (بند 9: لا كود؛ والمساحة مغطاة بـPRs مفتوحة).

## 8) ما تلمسه #207/#221 وأثره على هذا التحليل [MEASURED حي 04:5xZ]

- **#207 (مفتوحة، أُنشئت 2026-11-05T19:42Z؛ عنوان PR «feat(console): support bounded polling of standard descriptors» — مواضيع commits على فرعها صياغات قريبة لكن غير مطابقة حرفيًا):** ملفاتها = README.md، crates/ginux-core/src/lib.rs، crates/ginux-init/{main.rs, dispatch.rs, channel_hooks.rs, launch.rs}، scripts/test-launch.py، tests/fixtures/launch-fixture.c (جُلبت headها وقورنت بـmerge-base). **والأهم [MEASURED من diff فرعها]:** تضيف `bootstrap_poll_allowed(pid,address,count)` في channel_hooks بقراءة **PEEKDATA حلقيّة على مصفوفة pollfd في ذاكرة الـtracee**، موصلة في `native_arguments_allowed` لبوابة SYS_POLL — **أي أنها تكسر ثابت «القرار سجلي حصرًا» (§2) بعد الدمج لـSYS_POLL تحديدًا: أول مسار قراءة-ذاكرة-ثم-deny/passthrough في الشجرة**. خلاصة §5/§9 صحيحة على `64a3e3f7` وتستلزم إعادة قياس كاملة بعد دمجها.
- **#221 (مفتوحة، أُنشئت 2026-11-06T00:23:31Z، «fix(process): fail wait4 stores with EFAULT like Linux»):** ملفاتها = Makefile، crates/ginux-init/{main.rs, supervisor.rs}، scripts/test-process-native.py، tests/fixtures/process-review-fixture.c — **تلمس مباشرة صفوف §4-3/4 (سياسة فشل wait4 stores: من fail-closed إلى -EFAULT على غرار النواة)** ⇒ صفوف (أ) في §6 ومعيار T1 يتغيران بعد دمجها.
- **لا مرشح PR من هذا التحليل الآن:** أي PR في هذه المساحة أثناء فتحهما يخالف قيد عدم التداخل (v5.1-3)؛ **إعادة قياس إلزامية للصفوف المذكورة فور حسم أيٍّ منهما على الشجرة الجديدة.**

## 9) الخلاصة

«المُحاكاة لا تتأثر بـTOCTOU» **مؤكدة على مستوى القرار على `64a3e3f7`** [MEASURED]: مدخلات القرار سجلية (باستثناء wait4-park kernel-state@2113–2161 بلا passthrough)، ولا نمط فحص-ذاكري-ثم-passthrough موجود في المسارات الأربعة؛ النواة هي الفاحص الوحيد للوسائط المؤشرية في المسارات المنفَّذة. **تنبيه مصيري: دمج #207 سيكسر هذا الثابت لـSYS_POLL (`bootstrap_poll_allowed` بقراءة pollfd)** — الخلاصة مقيدة بالشجرة المثبتة. المخاطر المتبقية أربع نوافذ كتابة/قراءة بعد الالتقاط داخل فضاء العناوين المذكورة في §6 (أ–د) [INFERRED]، معالجتها اليوم fail-closed في `64a3e3f7` وقابلة للتغير بدمج #221 (نوافذ أ/ب). هذا التحليل تحليل فقط: لا كود، لا اختبار منفَّذ، لا PR — والمرشحون الفعليون يأتون في تقرير المرحلة 4 خارج ملفات #207/#221.

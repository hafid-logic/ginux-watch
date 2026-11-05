# result.md — T-20261105-15 (critic v4.0 §3 — مراجعة مستقلة لنتائج W1–W4)

**as-of:** 2026-11-05T20:27–20:33Z. المنهج: إعادة جلب مستقلة (`gh api` + `git show` + إعادة حساب من ملفات evidence) ثم مقارنة حرفية. لم يُعدّل أي ملف عامل. المرجع upstream المثبت: `0e06a986` (وأُعيد التحقق أن HEAD الحالي `21e48f7c` = دمج #209، 20:18:52Z — لا يبطل أي ادعاء لأن الجميع ثبّتوا 0e06a986 ووثّقوا حركة main).

## خلاصة

كل الادعاءات الجوهرية [MEASURED] في النتائج الأربع أعدتُ التحقق منها بنفسي (12 فحصًا مستقلًا، الجدول أدناه): **صفر مطالبات كاذبة، صفر أرقام مخترعة**. الإشكال الوحيد: W4 ترك 3 أسطر ادعاء بلا وسم (مخالفة PROTOCOL §Result format "Every claim tagged") — إصلاحات أحادية السطر تُطبَّق نسخًا ولا تتطلب إعادة قياس. لا التباس hypothesis-vs-fact: كل الاستنتاجات موسومة [INFERRED]/[HYPOTHESIS] كما يجب (W2 §"بدون QEMU"، W1 جدول الأدلة 14–15، W3 "63×"). لا مشغّلات STOP-AND-REPORT في أيٍّ من النتائج — أؤكدها.

## per-worker verdicts

### W1 (T-20261105-11) — KEEP (0 إصلاحات)
- ptrace من الكود: أعدت جلب `crates/ginux-init/src/main.rs?ref=0e06a986` (3465 سطرًا): `PTRACE_GET_SYSCALL_INFO=0x420e` حرفيًا سطر 1594، فحص ABI `0xc000003e` ~1603، `registers.orig_rax = u64::MAX` سطر 1624، حلقة SYSEMU بـ`getpid→4242` في 3373–3420، تسلسل chroot→chdir→TRACEME→setgroups→setgid→setuid→NO_NEW_PRIVS في 2837–2854 — كلها [MEASURED] مطابقة. [MEASURED: contents API، 20:29Z]
- unsafe: أعدت العد من evidence/rs/ نفسها: إجمالي 183 في 21 ملفًا (launch.rs=84، main.rs=60، baseline-runner=17، process-native-fixture=11، supervisor=10، vfs-index=1) — مطابق 100%. [MEASURED]
- shجرة main: qemu=0 مسارًا، efi=1 (Makefile) — مطابق لجدول الأدلة. 199 مسارًا = 148 blob + 51 tree [MEASURED من tree-main.json] — يفسر "199" (W1) مقابل "148 ملفًا" (W4) دون تناقض.

### W2 (T-20261105-12) — KEEP (0 إصلاحات إلزامية؛ ملاحظة اختيارية واحدة)
- Run 42102046103 أعيد جلبه حيًا: `conclusion=failure`؛ jobs: discover=success، verify (main, 10.1.2)=failure، verify (main, 10.0.13)=failure — مطابق حرفيًا. [MEASURED: gh run view، 20:28Z]
- Artifacts حية: logs-main-qemu-10.0.13=5452 B، 10.1.2=5334 B — مطابق. [MEASURED: artifacts API، 20:31Z]
- e918d29: `--stat` = ملف واحد `.github/workflows/ginux-verify.yml` (5+/8−)، والdiff يحصر التغيير في تعليق مفتاح `schedule:` فقط — مطابق. التحقق التباعي: `git show 78c864f:.github/workflows/ginux-verify.yml` يُظهر `schedule:` بسطر 12 وتحته تعليقات فقط — قصة HTTP 422 corroborated من حالة المستودع. [MEASURED]
- اللوج: `doctor=2 check=0 test=2` في السطرين 910 و1828؛ `Makefile:14: doctor Error 1` (648) و`Makefile:98: test-intercept Error 2` (909)؛ `upstream_sha=0e06a986…` (626) و`26609015…` (1543)؛ 28× `test result: ok`؛ `reset-storage` صفر إصابات في Makefile @0e06a986 — كلها مطابقة. [MEASURED: evidence/run-42102046103-full.log]
- ملاحظة اختيارية (لا تمنع KEEP): نص HTTP 422 نفسه artifact عابر لا يُعاد جلبه؛ يُستحسن عند النقل إلى STYLE-NOTES ذكر "corroborated by 78c864f state" صراحةً بدل الاعتماد على رد API الميت.

### W3 (T-20261105-13) — KEEP (0 إصلاحات)
- أعدت حساب time-to-merge من API حية: #201 = 17:58:50→18:17:48 = **19.0 د** ✓، #204 = 18:27:31→19:15:59 = **48.5 د** ✓، #160 = 12:22:31→13:11:44 = **49.2 د** ✓ (وأحجامها +21/−4/1f، +190/−12/8f، +1/−1/1f مطابقة). [MEASURED: pulls API، 20:30Z]
- أعدت حساب الإحصاءات من جدولهم ذاته: median 39.25≈39.2، mean 48.05≈48.0، meleficarumvaldis (n=22) median 37.6/mean 34.4 — كلها دقيقة. "63×" = 2374/37.6 = 63.1 ✓ [INFERRED] موسوم.
- STYLE-NOTES.md: commit 236cd87 = `+33/−0` بخصوص هذا الملف (hunk واحد `@@ -215,3 +215,36 @@` إضافة خالصة بعد السطر 215، صفر حذف) — **append-only مؤكد**. [MEASURED: git show 236cd87]
- الانخراط حيًا: #153 = 3 تعليقات، #201 = 0 تعليقات/0 reviews، #154 veighnsche، #156 meleficarumvaldis — مطابق. closed-unmerged: evidence/closed-unmerged.txt يظهر `total_count=0` بتاريخ 20:20:20Z. [MEASURED]

### W4 (T-20261105-14) — REVISE (3 إصلاحات: وسوم ناقصة على 3 أسطر في §"أصولنا الآن")
كل الفحوص الفنية مطابقة: `#[test]`=0 في vfs-index (contents API حي) ✓؛ سطور `scan_tar:414`/`parse_pax:672`/`whiteout:344`/`assemble_layers:106`/`set_size_and_checksum:232` كلها دقيقة حرفيًا ✓؛ `remove_descendants` usage 118–123 (التعريف :367 — التسمية "موجودة (سطور 118–123)" تصف موقع الاستدعاء، مقبولة) ✓؛ vfs lib.rs `new:58`/`resolve:119`/`open:359`/`read:427` ✓؛ `checked_add` داخل parse_pax (682) ✓؛ `[profile.release]` @0e06a986 = codegen-units/lto/opt-level/panic=abort/strip **بلا overflow-checks** ✓؛ `test-unit` = 7 crates بلا vfs-index ✓؛ عناوين #167/#175/#193 كما نُقلت ✓. [MEASURED: contents API + live fetch، 20:29–20:32Z]

الإصلاحات الثلاثة بالضبط (للمشرف، ملف `team/results/T-20261105-14/result.md`، قسم "أصولنا الآن"):
1. سطر `archive/pr-a-protocol-state-tests/ (+71/−0؛ C1 checksum + C2 arp؛ mutants 0/0).` → ألحق: `[MEASURED: archive/pr-a-protocol-state-tests/README.md + pr-description.md (+71/−0 موثقة؛ mutants-after run 41916256214 = 0 على الدالتين)]` (تحققت: patch فيه 71 سطر + محتوى، والREADME ينص +71/−0 حرفيًا).
2. سطر `STATE F1–F9: كلها محسومة على الشجرة القديمة؛ F9/#54 أُصلحت upstream ثم ضاع إرثها (انظر فرصة 6).` → ألحق: `[OBSERVED: STATE.md F1–F9 + F9 سطر RESOLVED [MEASURED 2026-11-03T22:00:13Z]]`.
3. سطر `matrix P1–P17: الصفوف المرتبطة بالنواة (P5/P14…) صارت C moot على main.` → ألحق: `[OBSERVED: reports/cross-check/matrix.md + STATE.md جلسة 25]`.

## جدول الفحص العشوائي (spot-check)

| # | الفحص | المصدر المستقل | النتيجة |
|---|---|---|---|
| 1 | run 42102046103: failure؛ discover=success؛ verify×2=failure | gh run view حي 20:28Z | MATCH |
| 2 | e918d29: ملف واحد، تعليق `schedule:` فقط | git show --stat + diff | MATCH |
| 3 | 78c864f: مفتاح `schedule:` فارغ (سطر 12) | git show 78c864f:… | MATCH (corroborates 422) |
| 4 | ptrace: 0x420e@1594، u64::MAX@1624، SYSEMU@3373+ | contents API حي | MATCH |
| 5 | unsafe: 183/21؛ 84/60/17/11/10/1 | إعادة عدّ evidence/rs/ + API | MATCH |
| 6 | t2m #201=19.0/#204=48.5/#160=49.2 د | pulls API حي | MATCH |
| 7 | medians 39.2/48.0؛ 37.6/34.4 (n=22) | إعادة حساب من الجدول | MATCH |
| 8 | STYLE-NOTES append-only +33/−0 | git show 236cd87 | MATCH |
| 9 | #153=3 تعليقات؛ #201=0/0؛ مؤلفا #154/#156 | comments/reviews API حي | MATCH |
| 10 | vfs-index: 0 #[test]؛ scan_tar:414/parse_pax:672/whiteout:344/… | contents API حي | MATCH |
| 11 | [profile.release] بلا overflow-checks؛ test-unit بلا vfs-index | contents API حي | MATCH |
| 12 | doctor=2 check=0 test=2 ×2؛ Makefile:14/:98؛ SHAs 0e06a986/26609015؛ artifacts 5452/5334 B؛ 28× ok؛ reset-storage غائب | run log + artifacts API + Makefile حي | MATCH |

12/12 MATCH — لا MISMATCH.

## تحذيرات التكرار (duplication)

1. **فرصتا W4 رقم 1 و5 (fuzz على vfs-index + اختبارات وحدة) — أخطر بندين تكرارًا**: vfs-index أرض meleficarumvaldis حصرًا هذا اليوم (3 PRs مدموجة #167/#175/#193، إضافة إلى اختبارات scripts #160/#173/#195) وهو مستمر. حدّ W4 "متوسط" صحيح لكنه يُرفع إلى **عالٍ عمليًا**: قبل أي عمل، فحص حي لـPRs مفتوحة تلمس `crates/ginux-vfs-index`، وإلا احتمال سباق مباشر كبير. تبرير الاستمرار: اختباراتهم scripts-based ولا `#[test]` داخل vfs-index حتى 0e06a986 — النافذة قائمة لكنها تضيق.
2. **#207 (veighnsche، console polling) مفتوح** — W4 فاته الصواب بتجنّب منطقة stdio/console صراحةً؛ أؤكد: لا تقترح شيئًا في descriptors/stdio (أرض #205/#206/#207).
3. **فرصة 4 (differential)**: التداخل مع gates-todo 9/11 وbaseline-runner وثّقه W4 ذاتيًا؛ يبقى مشروطًا بسؤال توجيه (fork أم upstream) — نعم على "needs prior question".
4. **فرصة 6 (overflow-checks)**: صفر PR من الـ24 لمس أي Cargo.toml [MEASURED من prs-files-engagement.jsonl] — خطر تكرار منخفض فعلًا؛ لكنها إعادة أرضنا المنشورة #43/#54 وسوم "سؤال المستخدم أولًا" إلزامي كما وسمت W4.
5. **#209 اندمج 20:18:52Z (HEAD الآن 21e48f7c)**: موضوع سلامة السكربتات (ثيمة 3 عند W3) أُغلِق للتو — أي اقتراح مستقبلي في hash-verification أصبح moot.

## الاتساق الداخلي بين النتائج

- W1 "لا seccomp في الكود" ضد W2/W3/W4 "balanced profile": **لا تناقض** — profile جدول سياسة ثابت (`decide_balanced` في ginux-core مع fail-closed −ENOSYS) لا فلتر seccomp؛ W1 وحدها وثّقت هذا التمييز بالكود.
- W1 "199 مسارًا" ضد W4 "148 ملفًا": متوافقان (148 blob + 51 tree) [MEASURED].
- W1 "vfs-index=1 unsafe" ضد W4 "نقية unsafe=0": الإصابة الوحيدة سطر 631 نص `"unsafe rootfs path"` في رسالة خطأ — كلاهما صائب والشرح موجود عند W4.
- W2 SHAs مختلفان داخل run واحد (main تحرك mid-run): موثق باللوج، ولا يبطل تثبيت 0e06a986 لدى W1/W4 لأن كليهما يصرّح بالتثبيت.

**GATE: REVISE (3 fixes)**

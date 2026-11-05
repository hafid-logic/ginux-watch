# إعادة تقييم Ginux بعد الاستئناف — 2026-11-05 (توجيه v4.0، جلسة 28)

المنهجية: 4 عمّال متوازين (T-20261105-11..14) + critic مستقل (T-15؛ فحوص 12/12 مطابقة؛ 3 وسوم أُضيفت لنتيجة W4). كل ادعاء [MEASURED] بدليل في team/results/. التحقق الحي: main `0e06a986` 20:09Z، و`21e48f7c` بعد دمج #209 في 20:18Z.

## 1) ما الذي تغيّر [MEASURED]
- **المنتج:** ginux لم يعد نواة؛ إنه **userspace kernel عبر ptrace**: حلقتا تتبّع في `crates/ginux-init/src/main.rs` (native `PTRACE_SYSCALL`+`GET_SYSCALL_INFO` أسطر 1594–1624؛ legacy `PTRACE_SYSEMU` 3373+)؛ الsyscall المرفوض يُمنع بـ`orig_rax=u64::MAX`، والمسموح يُنفَّذ حقيقيًا مع virtualization للقيمة المرجعة. shims بـ`asm!` بلا libc (`supervisor.rs:176–274`).
- **حدود الثقة:** chroot + `setgroups(0)/setgid(1000)/setuid(1000)` + `PR_SET_NO_NEW_PRIVS` + ptrace mediation (main.rs:2829–2856). **لا seccomp ولا userfaultfd ولا namespaces ولا cgroups حقيقي** (CgroupFs عرض in-memory). «العقد المرقّم» في الكود = `SCHEMA_VERSION=1` + `[contract] profile` + fail-closed `decide_balanced`.
- **unsafe:** 183 موضعًا/21 ملفًا (458KB)، مركّزة في ثنائيات الsupervisor (launch.rs 84، main.rs 60)؛ **كل مكتبات crates خالية من unsafe**.
- **ما أُزيل من النواة المستقلة:** `kernel/` (91 مسارًا)، `boot/efi`+`tools/qemu`، `services/`+17 crate (oci، wayland-domain…)؛ Rust من 10.5MB/95 ملفًا إلى 458KB/21 ملفًا (مقارنة main@0e06a986 مقابل bootable-kernel@4d4a53bb).
- **العملية:** 24 PR مدموجًا منذ d337713b (22 meleficarumvaldis + 2 veighnsche)؛ **وسيط القبول 39.2 دقيقة**، الوسيط 55.5 سطرًا؛ التصنيف fix 18/test 3/feature 2/chore 1؛ دمجات صامتة على دفعات ساعية (0 مراجعات، تعليقات فقط على #153/#154)؛ 0 أُغلقت دون دمج؛ لا حماية فرع (protection 404). CI لديهم = `check.yml` بلا QEMU (check+test-unit على macOS، اختبارات native على ubuntu).
- **تحققنا بالتشغيل:** ginux-verify على main فشل (run [42102046103](https://github.com/hafid-logic/ginux-watch/actions/runs/42102046103): doctor=2/check=0/test=2) — **main يتوقع VM بـRocky 10.2 تحت QEMU ومضيف مرجعي Darwin-arm64**؛ بوابات إقلاع UEFI القديمة زالت. أي أن شهادة 3b على tag الأرشيف تبقى صالحة، وبوابة QEMU القديمة أصبحت obsoleted على main.

## 2) ما ينتقل من عملنا وما لا ينتقل
**ينتقل:** منهجية الفريق (بطاقات/critic/أدلة)؛ STYLE-NOTES (مُحدَّث بقسم userspace era)؛ فكرة الfuzz harnesses بإعادة توجيه؛ **Miri/ASan صار ممكنًا** (مستحيل سابقًا على النواة العارية)؛ أرشيف المرحلة 1 صالح مع شهادته.
**لا ينتقل:** أهداف fuzz الثلاثة القديمة كما هي (oci/protocol/volume ماتت على main؛ الخليفة الوحيد: tar/PAX/whiteout في `ginux-vfs-index`+`ginux-vfs` — **0 `#[test]` وغير مدرج في `test-unit`**)؛ PR-A protocol-state (لا خليفة على main — أرشيف فقط)؛ ginux-verify المبني على QEMU كبوابة main (استُبدل منطقيًا بـcheck/unit/native).

## 3) الفرص الخمس (المختارة من 6 مرشحات W4)
| # | الفكرة | الدليل | الجهد | خطر التكرار | سؤال مسبق؟ | توقع القبول |
|---|---|---|---|---|---|---|
| 1 | **Miri/ASan داخلي** على 14 crate نقية (workflow في ginux-watch؛ النتائج → قوائم findings، وما يُنشر يمر بapproved/) | 0 unsafe/0 extern في المكتبات [W1+W4] | 4–6h | صفر — لا شيء مشابه لديهم | لا | findings تتحول إلى fix صغيرة بنمط يقبل بـ~39min |
| 2 | **`overflow-checks=true` في `[profile.release]`** — إرث #54 ضاع في الpivot | profile @0e06a986 بلا overflow-checks [W4] | ~1h | منخفض لكن يمس #43/#54 المنشورتين | **نعم — قرار المستخدم** | مرتفع (نمط fix ≤60 سطرًا؛ صياغة «استعادة ضائعة في pivot») |
| 3 | **Fuzz retarget إلى vfs-index** (`scan_tar:414`/`parse_pax:672`/`whiteout:344`) | 0 #[test] + خارج test-unit [W4، تحقق critic] | 3–4h | متوسط–مرتفع (meleficarumvaldis يملك vfs-index: #167/#175/#193) | لا — يُبنى داخليًا؛ crashes فقط تُبلَّغ | crashes/POCs تُقبل سريعًا؛ البقاء داخليًا يزيل التعارض |
| 4 | **إطار تفاضلي native-vs-ginux** على fixtures موجودة | fixtures + بوابة native لديهم [W4] | 6–8h | متوسط (يحاذي gates-todo لديهم) | لا — تأجيل حتى تكتمل خرائطهم | متوسط |
| 5 | **تثبيت أرشيفي:** pin PR-A + harnesses على bootable-kernel@4d4a53bb (توجيه fuzz-branch-verify نحو الtag) | الأرشيف + شهادة 3b | ~1h | صفر — داخلي | لا | غير مطلوب |

## 4) لا نفعل
لا مساس بـstdio/console (#207 يملكه) ولا بـrocky-image scripts (#199/#201/#209)؛ لا PR على vfs-index أثناء الموجة الساعية لـmeleficarumvaldis؛ لا تكرار لمنشوراتنا الستة (#4/#14/#43/#54/#58/#61)؛ لا إعادة بناء بوابة QEMU على main؛ لا نشر بأي شكل بدون نص حرفي معتمد في approved/ (POLICY 0–3).

## 5) بطاقة قرار للمستخدم (≤10 أسطر)
1. **الإجراء الأول الموصى به:** فرصة 1 — workflow Miri/ASan داخلي في ginux-watch (بلا نشر، بلا تعارض، ويبني رصيد findings).
2. فرصة 5 (تثبيت أرشيفي) منخفضة الكلفة — يمكن ضمها للإجراء الأول.
3. **القرار المعلق الوحيد:** فرصة 2 (`overflow-checks=true`) — النص المقترح جاهز في drafts/2026-11-05-overflow-checks-draft.md (غير منشور)؛ لا يُنشر إلا باعتمادك الحرفي.
4. فرصة 3 (fuzz vfs-index): أنصح بتأخير البدء 7 أيام حتى تهدأ موجة meleficarumvaldis، ثم بناء داخلي.
5. فرصة 4: مؤجلة بلا كلفة.

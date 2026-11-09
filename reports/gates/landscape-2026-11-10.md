# خريطة البوابات (gates landscape) — 2026-11-10

- base_head: 55b719db9c52889543fbb177fab4cf2b2f90955e (upstream main لحظة الجمع)
- المنهجية: clone قراءة-فقط blobless+sparse على hdae/ + git log/ls-remote فقط؛ ربط PR→gate من نصوص hdae؛ أي حالة open/merged للـPRs من خارج git = [UNVERIFIED] (يلزم API داخل Actions بـGITHUB_TOKEN داخلي وفق v7.0-5a).
- العمال: G1 (خريطة) + G2 (أسلوب) + G3 (فجوات) + G4 (جدوى) + critic — منهجية v7.0 §5.

## الأعداد [MEASURED]
- gates-todo: 6 (11، 12، 12.1، 12.25، 12.5، 13) — gates-deferred: 1 (14 Unicorn) — gates-done: 17.
- حسب الحالة المكتوبة في الملفات: partial=1 (Gate 11) | technically-passed بانتظار قبول بشري=4 (12، 12.1، 12.25، 12.5) | not started=1 (Gate 13) | deferred=1 (14).

## ما ينتظر قرارًا بشريًا من المالك [MEASURED من نصوص الملفات]
1. Gate 11: اختيار ما إذا كان يتطلب تأكيدًا على native x86-64/KVM ("Required human decision" في STATUS.md Context recovery) + لا استثناءات tolerance معتمدة ("no workload-specific tolerance exceptions are approved").
2. Gates 12/12.1/12.25/12.5: "[ ] Obtain human review and acceptance" — البوابات "technically passed" والدمج ممنوع على الوكيل ("Do not merge or close any pull request").
3. Gate 14 (deferred): "must be explicitly reactivated before implementation".
ملاحظة زمنية [MEASURED]: merge commits للـPRs 249/251/252/253/254 (2026-11-09 10:03–10:05) أسلاف لـHEAD 55b719db بينما سجلات hdae في الشجرة ما زالت "pending" — السجلات لم تُحدَّث بعد الدمج.

## جدول البوابات غير المنتهية

| id | العنوان | الحالة | آخر تغيير | نوع الدليل المطلوب | قرار بشري | معيار قبول قابل للقياس (مختصر) |
|---|---|---|---|---|---|---|
| 11 | Performance characterization | partial | 9759daae 2026-11-08 | sysbench matched matrix + `make bench-compare` | نعم (KVM/tolerance) | كل صف ≤4% أسوأ من native؛ 5 صفوف thread فشلت 0.917x–0.953x [gate-11:390-392] |
| 12 | Contract/network UX | technically passed | 3fae1384 2026-11-08 | test-config/instance/network/systemd + demo بشري | نعم (قبول) | unmatched glob fail-closed؛ explicit deny wins؛ multi-flag atomic |
| 12.1 | Virtual kernel filesystems | technically passed | 94448a6b 2026-11-09 | component tests + Rocky QEMU regression | نعم (قبول) | صفر ملفات proc/sys باقية؛ ps بلا ENOSYS |
| 12.25 | Top-level instance CLI | technically passed | 5ff2b05a 2026-11-09 | CLI fixtures + test-instance/config/systemd | نعم (قبول) | create بلا recipe؛ import ذرّي؛ بلا aliases قديمة تفشل |
| 12.5 | Contract maintenance lock | technically passed | 219236ab 2026-11-09 | test-gate125-lock + Rocky interactive | نعم (قبول) | default locked fail-closed؛ lock/unlock فقط while stopped؛ relock حرفي |
| 13 | Boundary hardening | not started | 94f942ce 2026-11-06 | malformed-input suites + bounded fuzz + escape fixtures | للبدء: لا؛ للإغلاق: نعم | fuzz بلا untriaged crash؛ escape لا يُتم host syscall غير مُوسَّط |
| 14 | Unicorn backend | deferred | 94f942ce 2026-11-06 | backend-differential tests + benchmarks | نعم (إعادة تفعيل) | نفس fixture على native/Unicorn بقرارات مكافئة |

## PRs الظاهرة عبر ls-remote فقط [MEASURED]
249=9759daae، 250=a2cf4e80، 251=3fae1384، 252=94448a6b، 253=5ff2b05a، 254=219236ab، 255=f9f43319 (غير مدموج؛ يلمس hdae/STATUS.md + gate-13)، 256=96ff34d2 (دمجه = HEAD). حالة open/closed = [UNVERIFIED] بلا API.

## المرشحون للمساهمة (بعد critic — لا بناء ولا نشر قبل اعتماد المالك)
1. **C2 (أولوية)** — إكمال evidence لـ`make bench-block`/`make bench-network` على ubuntu-24.04+Rocky TCG وإلحاقه في ملف البوابة 11: يخدم بند خطة التحقق الحرفي "device-path measurements are included in comparison evidence" [gate-11:242-243] والقسم Evidence بلا قياس device (سطور 256–419). جهد S، تعارض صفر مع PR#255، سلّم: hypothesis→measured.
2. **C1 (ثانيًا، بعد C2 — نفس الملف يُحرر تباعًا)** — إعادة إنتاج مصفوفة threads الفاشلة (0.917x–0.953x) على ubuntu-24.04 x86-64 QEMU TCG ببروتوكول Gate 11 حرفيًا؛ metadata يسجل البيئة؛ bench-compare exit≠0 يُسجل كسلوك متوقع. جهد M، سلّم: hypothesis→measured. يجمع أدلة لقرار KVM المعلق — لا يقترح قرارًا.
3. **C3 (بعد REVISE الإلزامي)** — harness تفنيدي لأرضية seccomp خارج TCG: إضافته prctl(PR_SET_NO_NEW_PRIVS) قبل PR_SET_SECCOMP (وإلا يفشل على runner بلا CAP_SYS_ADMIN)، ≥15 تكرار/arm، نتيجة-null غير حاسمة تعلن بصدق. ملفان جديدان بلا تعديل Makefile. جهد S، diagnostic داخلي.
قواعد critic المطبقة: تعارض C1↔C2 الداخلي (نفس الملف) يعالج بالتتابع؛ كل المخرجات مسودات محلية — أي رفع upstream يحتاج موافقة حرفية من المالك (قاعدة 15/16 من AGENTS).
تصحيح critic: عبارة "لا CI run IDs إطلاقًا" غير دقيقة — run ID واحد موجود في gates-done/8.5-unified-repository-transition.md:124؛ الصحيح: بلا run IDs في ملفات Gates 11/12.x الحالية.

## دورة التحديث الأسبوعية (v7.0-5e)
أسبوعيًا: تحديث هذا الملف + maintainer-profile.md من main الحي (clone sparse جديد)، وقسم «البوابات» الثابت في التقرير اليومي (بوابات تغيّرت، PRs جديدة للمالك، طلب جديد، حالة المرشحين). ربط PR→gate وحالة الدمج عبر workflow بـGITHUB_TOKEN داخلي عند أول حاجة.

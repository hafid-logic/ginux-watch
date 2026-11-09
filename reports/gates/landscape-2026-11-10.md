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

قرار v7.1-3a (2026-11-10): البنود 1–2 أعلاه مسجلة رسميًا «بانتظار المالك» في STATE وفهرس البوابات هذا — لا نتابعة منا ولا تحويل للمشرف (SUPERVISOR-RULES قاعدة 7)؛ البند 3 (Gate 14 deferred) كما هو حتى إعادة تفعيل صريحة.

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

## المرشحون (تحديث v7.1-3b/3c، 2026-11-10)
- **C2 (الوحيد القائم)** — إكمال evidence لـ`make bench-block`/`make bench-network` على ubuntu-24.04+Rocky TCG وإلحاقه في ملف البوابة 11؛ صفحة التصميم الكاملة (الاقتباس الحرفي، التغطية بالـPRs، الجهد والمخاطر، سؤال المالك): **reports/gates/c2-design-2026-11-10.md** — لا بناء ولا فرع ولا نشر قبل موافقة المالك الصريحة (v7.1-3c).
- **C1: مُسقطة بقرار المستخدم (v7.1-3b)** — تراجعنا عن متابعة Gate 11 وPR#249؛ النص التاريخي الكامل من v7.0 في git history (إعادة إنتاج مصفوفة threads على TCG ببروتوكول البوابة حرفيًا، جهد M).
- **C3: مُسقطة بقرار المستخدم (v7.1-3b)** — harness seccomp التفندي؛ لا تحضير.
- **#249/#250/#251–254**: عينات لمعايرة أسلوب المالك فقط (maintainer-profile.md) — ليست بنود متابعة.
قواعد critic (v7.0) باقية مرجعًا منهجيًا؛ تصحيح critic السابق: بلا run IDs في ملفات Gates 11/12.x الحالية (واحد فقط في 8.5:124).

## دورة التحديث الأسبوعية (v7.0-5e)
أسبوعيًا: تحديث هذا الملف + maintainer-profile.md من main الحي (clone sparse جديد)، وقسم «البوابات» الثابت في التقرير اليومي (بوابات تغيّرت، PRs جديدة للمالك، طلب جديد، حالة المرشحين). ربط PR→gate وحالة الدمج عبر workflow بـGITHUB_TOKEN داخلي عند أول حاجة.
- **مؤشر v7.1-3c.1 (قياس فقط): «PRs مدموجة دون تحديث سجلات hdae»** — يُحسب أسبوعيًا: merge commits على upstream/main منذ آخر فحص لم تتبعها تحديثات حالة في hdae/ (الملفات ما زالت pending). القياس الحالي [MEASURED @55b719db]: **5** (PRs 249، 251، 252، 253، 254 — مدموجة 2026-11-09 10:03–10:05Z وسجلات hdae ما زالت pending).

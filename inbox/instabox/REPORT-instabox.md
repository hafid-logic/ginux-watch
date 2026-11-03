# REPORT-instabox.md — فحص ملاءمة منصة InstaBox لتشغيل Ginux داخل QEMU/KVM

التاريخ: 2026-10-30 05:32–05:50 UTC (06:32–06:50 بتوقيت Africa/Algiers).
النطاق: فحص ملاءمة فقط (لا benchmark نهائي). القاعدة المالية: الخطة المجانية فقط — **لم يُنفَق شيء**.

---

## 1. القرار

> **(C) لا تصلح.**

الدليل الحاسم (سطر واحد): وثائق المنصة الرسمية الحية تنص صراحةً: «There is also no `/dev/kvm` in the guest … so Firecracker, **QEMU with KVM** … cannot run; QEMU in pure emulation (`-accel tcg`) works, slowly.» — https://instabox.sh/docs/sdk.md
هذا يُسقط R1 (شرط الحسم) قبل إنشاء أي جهاز، وفق بوابة المرحلة 1 في التوجيه. لم تُنشأ آلة، ولم يُستخدم المفتاح.

---

## 2. جدول المتطلبات R1–R7

| المتطلب | الحالة | الدليل (أمر + مقتطف) |
|---|---|---|
| **R1** KVM يعمل: QMP `query-kvm` → `enabled:true, present:true` | **لا** [OBSERVED] | `rg 'kvm\|KVM\|nested\|/dev/kvm' llms-full.txt` → موضع واحد (سطر 1180): «no nested KVM … no `/dev/kvm` … QEMU with KVM … cannot run» — نص وثائقي صريح يمنع الوصول إلى اختبار QMP أصلًا |
| **R2** ≥4 vCPU و≥7 GiB | نعم وفق الوثائق [OBSERVED]؛ تحقق يدوي لم يُنفذ [UNVERIFIED] | خطة Free: «1 machine, 4 vCPU / 8 GiB»، «`free -m` shows about 7.8 GiB» (llms-full.txt سطرا 1747، 1882) |
| **R3** بناء QEMU ≥v10.0.12 ممكن (تجنّب v10.0.13) | غير محسوم [UNVERIFIED]؛ **غير ذي صلة** بعد فشل R1 | الوثائق لا تذكر إصدار QEMU في apt لـ Debian 13؛ وما يمكن بناؤه يعمل فقط بـ `-accel tcg` («works, slowly») [OBSERVED] |
| **R4** وصول إلى github.com وrust-lang وcrates.io وQEMU وdeb.debian.io وregistry-1.docker.io وquay.io وghcr.io | على الأرجح متاح [INFERRED]؛ لم يُقَس [UNVERIFIED] | الوثائق: الدخول غير محدود، rustup يعمل داخل الصندوق («`rustup toolchain install` … need no sudo») [OBSERVED]؛ لا آلية حجب افتراضية في الوثائق (الـ outbound proxy خاص بـ Org Secrets فقط) [OBSERVED] |
| **R5** أوامر طويلة بالخلفية | نعم وفق الوثائق [OBSERVED] | «`instabox exec --background`» + «`instabox jobs`» (سطر 990)؛ مهلة الأمر الواحد «at most 600» ثانية — مطابقة لحد 10 دقائق المفترض |
| **R6** ضجيج: CV ≤5%، steal ≤2% | **غير قابل للقياس** [UNVERIFIED] | يتطلب جهازًا يعمل؛ أُغلق بالبوابة. المضيف Firecracker مشترك؛ لا بيانات ضجيج في الوثائق («لا ذكر») |
| **R7** قرص ≥20 GiB؛ TMPDIR | نعم وفق الوثائق [OBSERVED]؛ فحص tmpfs لم يُنفذ [UNVERIFIED] | «20 GiB persistent ext4 disk at `/data`» و«20 GiB disk (fixed)» في Free (سطرا 1882، 1749) |

ملاحظة على R1: كل مقارنة أداء Ginux↔Linux المطلوبة تعتمد KVM. خيار TCG موجود نظريًا، لكنه «slowly» بنصهم، ونملك TCG محليًا مجانًا بالفعل (الجولات السابقة: QEMU 10.0.13 TCG + OVMF) — لا قيمة إضافية من دفع مقابل TCG سحابي.

---

## 3. خصائص الجهاز والتكلفة الفعلية

- **لم يُنشأ جهاز** (بوابة المرحلة 1 أغلقت قبل المرحلة 2)، لذا لا قياسات `lscpu`/`free`/`df` ولا `rustc --version` — سجلها في التوجيه كقيم [UNVERIFIED].
- ما هو معروف من الوثائق فقط [OBSERVED]: كل قالب (عدا `ci` الذي Ubuntu 24.04) هو Debian 13 (trixie) amd64 بنواة `6.18.54-instabox` داخل **Firecracker microVM**؛ Rust toolchain في `/opt/rust` على قوالب `agent-browser`/`universal`/`t3`؛ sudo بلا كلمة مرور عبر apt.
- **التكلفة الفعلية: $0.00** [INFERRED] — لم يُنشأ مورد ولا شُغِّلت آلة؛ أمر `instabox usage` لم يُستدعَ لأن CLI لم يُثبَّت أصلًا (لا داعي له بعد إغلاق القرار، وثبات قاعدة «ممنوع الإنفاق»).
- الحدود التي كانت ستحكم الجلسة (من الوثائق، للأرشيف): idle pause 30 دقيقة ثابتة في Free، max-run 480 دقيقة ثابتة، جهاز واحد بحجم `instabox-medium` فقط.

---

## 4. نتائج KVM (المرحلة 3)

**لم تُنفَّذ** — أُغلقت بالبوابة. لا يوجد `/dev/kvm` حسب الوثائق، فاختبار `qemu-system-x86_64 -accel kvm … query-kvm` مستحيل المضمول، ولن يضيف شيئًا فوق النص الوثائقي الصريح. نص الوثيقة الخام (كاملًا، من https://instabox.sh/docs/sdk.md):

> «**No kernel tracing, no nested KVM.** … There is also no `/dev/kvm` in the guest (the kernel is a KVM guest, not a KVM host), so Firecracker, QEMU with KVM, Docker-in-VM runtimes that need it, and nested microVMs cannot run; QEMU in pure emulation (`-accel tcg`) works, slowly.»

---

## 5. نتائج Ginux (4.4–4.5)

**لم تُنفَّذ** — تابعة لنجاح المرحلة 3. لا بوابة من بوابات Ginux (OVMF → controller prompt → test-linux-runtime/alpine/rocky) اختُبرت على المنصة. إصدار QEMU المستخدم: لا شيء (لم يُثبَّت). الوضع المرجعي المتبقّي هو بيئتنا المحلية (QEMU 10.0.13 TCG) مع مشكلة `verify_network_queue_rejections` المفتوحة من الجولة السابقة — خارج نطاق هذا التقرير.

---

## 6. الضجيج (المرحلة 5)

**لم تُقَس** — تتطلب KVM يعمل (5.4) وآلة حية (5.1–5.3). لا أرقام CV/IQR/steal صدرت، ولن تُنشر أي نتيجة من هذه المنصة. حد التصميم الذي كان سيُطبق لو متّصلنا: آلة مشتركة على مضيف Firecracker + طبقة افتراض إضافية (QEMU داخل الصندوق) — أي ضجيج تركيبي لا يُقاس إلا قياسًا فعليًا.

---

## 7. ما لم أستطع فعله وحدود الاستنتاج

1. **لم يُنفَّذ أي اختبار داخل آلة حية** (المراحل 2–5 كلها): لا تحقق يدوي لـ R2/R3/R4/R7، ولا قياس ضجيج R6، ولا أي بوابات Ginux. السبب: بوابة المرحلة 1 الوثائقية.
2. **حدود الاستنتاج**: قرار (C) مبني على الوثائق الرسمية الحية وليس على قياس داخل صندوق. نظريًا قد تكون الوثائق أقل من الواقع (إن كان المضيف يكشف vmx للأدنى فـ `/dev/kvm` قد يعمل رغم النص) — لكن النص صريح ولا يوجد مسار موثّق يوازيه، والتحقق يتطلب جهازًا وهذا ما يعنيه القرار (C) تجنّبه. أعتبر النص قاطعًا لأغراض هذا التوجيه.
3. لم أتواصل مع الدعم ولم أفتح ticket (قاعدة 5) — السؤال المقترح أدناه.
4. لم يُجرَ فحص أسعار الخطط المدفوعة إلا من صفحة التسعير المنشورة للجميع؛ لا أرقام مطلقة صدرت من قياس.
5. تنبيه صغير عن الشبكة المحلية: `api.instabox.sh` لم يُدعَ إطلاقًا (لا حاجة)؛ `instabox.sh` استجاب بسرعة (HTTP 200 في 0.053s). لا `x-deny-reason` وُجد — لا حجب شبكي صادفنا.

---

## 8. التوصية (بدائل قابلة للتحقق بروابط وثائقية)

المطلوب: مزوّد يعلن صراحة nested virtualization أو يبيع bare metal.

1. **GCP Compute Engine** — وثائق رسمية لـ nested virtualization مع خطوات تمكين وتأكيد (`/dev/kvm` داخل L1):
   - Overview: https://docs.cloud.google.com/compute/docs/instances/nested-virtualization/overview
   - التمكين: https://docs.cloud.google.com/compute/docs/instances/nested-virtualization/enabling
   (مدعوم تاريخيًا على أنوية L1 مع KVM — بيان المنصة: «Compute Engine's nested virtualization currently supports KVM» في منشورهم الرسمي: https://cloud.google.com/blog/products/gcp/introducing-nested-virtualization-for)
2. **AWS EC2 من نوع `*.metal`** — وثائق nested virtualization الرسمية: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nested-virtualization.html (المعادن تكشف VT-x مباشرة).
3. **Azure أحجام Dv3/Ev3 وأحدث** — بيان Microsoft الرسمي عن nested virtualization في Azure: https://azure.microsoft.com/en-gb/blog/nested-virtualization-in-azure/ (Hyper-V nested؛ لأحمال KVM يُفضَّل التحقق من vmx داخل الجهاز قبل الالتزام).
4. **خيار bare metal تقليدي** (Hetzner/OVH dedicated): يمنحك مضيفًا كاملًا بلا طبقة افتراض عليك — لقاعدة «لا توصية بلا رابط» أذكر صفحتي المنتج: https://www.hetzner.com/dedicated/ و https://www.ovhcloud.com/en/bare-metal/ (KVM ممكن لأنك تملك المضيف؛ لا صفحة «nested» منفصلة عندهما).

الأرخص عادةً للتجربة القصيرة: `*.metal` صغير في AWS أثناء جلسات القياس فقط، أو GCP بنوع يدعم nested. في الحالتين تُطبَّق نفس بوابات T-Q/T-I السابقة (تجنّب QEMU 10.0.13).

---

## 9. سؤال مقترح للدعم (إنجليزي)

> Your docs at https://instabox.sh/docs/sdk.md state that sandboxes run as KVM guests with no `/dev/kvm` and cannot run QEMU with KVM. Do you offer — or plan to offer — any template, plan, or host type with nested virtualization exposed (i.e., `/dev/kvm` and `vmx`/`svm` visible to the guest), or bare-metal access? If yes, which plan/template, and are there host-type or size restrictions?

---

## 10. النظافة والتنفيذ (قاعدة 4)

- **لا موارد أنشئت**: لا آلة، لا snapshots ⇒ لا `instabox rm` ولا `X-Confirm-Delete` لزم. تحقق `instabox ls`/`instabox usage` لم يُنفذ (CLI غير مثبّت؛ لا شيء لفحصه).
- **المفتاح**: وُرِّد في رسالة التوجيه فقط؛ **لم يُكتب في أي ملف ولا سجل ولا تقرير، ولم يُمرَّر إلى البيئة أصلًا** لأن المراحل 2–5 لم تُنفذ. تحقق نهائي أدناه (عدّاد مطابقات `ibk_` في شجرة المشروع = 0، و`printenv INSTABOX_API_KEY` = فارغ).
- لا اتصال بالدعم، لا tickets، لا إنفاق.

## 11. الملفات والروابط

- `artifacts/llms-full.txt` — لقطة الوثائق كاملة (SHA256 في `SHA256SUMS`).
- `artifacts/phase1-evidence.txt` — أوامر المرحلة 1 ومخرجاتها الخام.
- `artifacts/phase1.md` — سجل المرحلة 1 المفصل.
- مصادر حية: https://instabox.sh/llms-full.txt ، https://instabox.sh/docs/sdk.md (فقرات KVM)، https://instabox.sh/docs/limits.md (قوالب/أحجام/50 Mbit/s)، https://instabox.sh/docs/pricing.md (خطط/حدود).

## 12. ملخص المراحل (5 أسطر لكل مرحلة حسب التوجيه)

**المرحلة 1 (منفذة):** الوثائق حُملت (HTTP 200، 235,122 B) وفُحصت بـ grep. ذكر KVM/nested واحد صريح في sdk.md: لا `/dev/kvm` ولا nested KVM، و«QEMU with KVM … cannot run». الخطط: Free = جهاز واحد 4 vCPU/8 GiB، قرص 20 GiB ثابت، idle 30 دقيقة، max-run 480. الخروج 50 Mbit/s/VM والدخول غير محدود، وexec ≤600s مع `--background`+`jobs` للمهام الأطول.
**القرار عند البوابة: (C) لا تصلح** — R1 يفشل بنص صريح.
**المرحلة 2–5 (متخطاة بالبوابة):** لا آلة أنشئت، لا مفتاح استُخدم، لا إنفاق، لا بوابات Ginux نُفذت، لا ضجيج قيس.
**المرحلة 6 (منفذة):** هذا التقرير + artifacts + SHA256SUMS + تحقق النظافة (لا موارد، لا مفاتيح في الشجرة/البيئة).
**البديل المقترح:** GCP nested-virt أو AWS `*.metal` أو bare metal — بروابط وثائقية في القسم 8.

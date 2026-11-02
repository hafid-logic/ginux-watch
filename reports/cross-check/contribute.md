# contribute.md — فرص المساهمة (A/B مفتوحة) ومسودات تعليق ≤100 كلمة

آخر فحص: 2026-11-02T01:05Z على main@fbe6472e. **لا شيء منشور**؛ كل مسودة تتطلب نصًا معتمدًا من المستخدم (POLICY) وتخضع لبوابة منع التكرار قبل أي اقتراح.

> **حالة الملف (2026-11-03، أمر المستخدم v2.2 §1):** الفرصتان Opp-1 وOpp-2 **أُسقطتا (dropped) نهائيًا** ولن تُعرضا للنشر؛ المسودتان أدناه أرشيف فقط. السبب الموثق تحت عنوان كل فرصة، والمُسجّل أيضًا في matrix/STATE/HANDOFF.

## Opp-1 — P8 → تعليق على #14: doctor لا يسجّل/يفحص إصدارات QEMU/OVMF

> **أُسقط (dropped) 2026-11-03:** يكرر فكرة doctor-versions المنشورة في تعليقنا على issue #4 (2026-10-31T00:55:19Z) — كما قاس critic T-04 (results/T-20261102-04-par R3)؛ لا يضيف معلومة جديدة.
- **ماذا نضيف (جديد فعلًا):** فجوة قابلة للفحص في `tools/qemu/doctor.sh` (يفحص الوجود فقط، لا الإصدارات) [MEASURED@main] + تناقضنا المقيس بين بيئتين (10.0.13 vs 10.1.2/8.2.2 وOVMF مختلف) — يكمّل نقطة البيانات التي نشرناها على #14 (00:31Z) بمنعّكسها: جعل سجل الإقلاع ذاتي-الوصف. **لا يكرر** تعليقنا السابق ولا بنود #5.
- **المسودة (EN، ≤100 كلمة، بانتظار الاعتماد — السقف اليومي مستهلك):**
> One gap that may explain cross-environment differences like this issue: `tools/qemu/doctor.sh` currently checks only that `qemu-system-x86_64` exists — it neither records nor checks the QEMU and OVMF versions (verified at main@fbe6472e). Our passing runs (QEMU 10.0.13/10.1.2, Ubuntu OVMF 2025-09-23) and the failures here (QEMU 8.2.2 IOMMU width) differ mainly in toolchain behavior, not code. A small doctor enhancement — echo `qemu-system-x86_64 --version` plus OVMF file dates/sizes, optionally failing on an unpinned allowlist — would make boot logs self-describing and comparisons easier to interpret. Happy to draft it if useful.

## Opp-2 — P5 → تعليق على #28 (أو #29): FrameLease Copy يُلغي فرض الملكية نوعيًا

> **أُسقط (dropped) 2026-11-03:** يتجاهل فرض `can_release` وقت التشغيل (memory.rs:528-550) — كما قاس critic T-04 (results/T-20261102-04-seq)؛ التأطير يبالغ في الفجوة.

- **ماذا نضيف (جديد فعلًا):** زاوية مقطعية على عائلة ملكية الإطارات (#26–#29): `FrameLease` ما زال `derive(Clone, Copy)`@main — الإصلاحات الفردية (#37) تغلق مسارات، والنوع يمكنه إمساك الصنف كله وقت الترجمة. ثقة التأطير متوسطة (التصميم مقصود للسجلات المعبأة) — القرار لكم.
- **المسودة (EN، ≤100 كلمة، بانتظار الاعتماد):**
> Cross-cutting note on the frame-ownership family (#26/#27/#28/#29): `FrameLease` still derives `Clone, Copy` (kernel/src/memory.rs at main@fbe6472e), so lease ownership is by convention rather than enforced by types — the compiler cannot flag a copied lease that outlives its frame or double-releases it. Individual fail-closed fixes (#37) close single paths; making `FrameLease` a non-Copy (affine) type, or at minimum `debug_assert!`-ing exactly-once consumption, would let the compiler catch whole classes of these bugs at build time. If a broader refactor is out of scope, an exactly-once-consumption test may be a cheap interim.

## بنود B أُسقطت من المساهمات (بوابة منع التكرار — لا تضيف معلومة جديدة)
- P3 (SAFETY census): #5 يحمل نفس التوزيع لكل ملف (address_space 301/11، linux_socket 142/0، cpu 140/31) — أُسقط.
- P2/P4 على #17/#20/#22: لديها repro ديناميكي أدق من إحصائنا الساكن — أُسقط.
- P6 (static mut): #5 يقيس ~67 + ratchet في #9 — أُسقط.
- P11 (cpu.rs): #5 بند 5 قيد المعالجة — أُسقط.
- P13 (compat): أُصلح في #9 — أُسقط.
- #14 env-data: نشرناه 2026-11-02T00:31Z — لا تعليق ثانٍ.

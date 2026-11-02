# not-reported.md — مشاكل C غير المطروحة على upstream (مرتبة بالخطورة)

آخر فحص: 2026-11-02T01:05Z على main@fbe6472e + فحص شرطي تكميلي 02:12Z على fbe6472e و1203e291 (رأس upstream تقدّم 9 commits بينهما). **P10 معتمدة ومجدولة للنشر 2026-11-03**؛ لا شيء آخر نُشر (POLICY: نص معتمد فقط يُنشر).

## C-1 — P10: release بلا overflow-checks (الخطورة: متوسطة-منخفضة — robustness)
- **الحالة: معتمدة — حكم المستخدم 2026-11-02T02:12Z («عدّل ثم اعتمد») بعد تصحيح ثلاثة ضعفاء في المسودة الأولى** (تحقق ناقص، رقم 3,293 قديم استدلالي على d11c126a، ادعاء "تجاوز منطق الحدود" غير مثبت مع أمثلة gzip/PAX مُصلحة على الأرجح في #17/#20/#21). النص الجديد سؤال صيغ بالتخفيد المناسب مع إفصاح AI كما في #14، محفوظ حرفيًا في `approved/2026-11-03-1.md`؛ **النشر الأبكر 2026-11-03** (سقف 11-02 مستنفد) — مجدول job 494920 على 08:00Z مع بوابات: auth، منع التكرار، إعادة التحقق من الأطروحة على main اللحظي.
- **الشرط 1أ — لا تفعيل في أي سطح بناء [MEASURED على fbe6472e و1203e291 معًا]:**
  - `git show <rev>:Cargo.toml`: [profile.release] = codegen-units=1/lto=true/opt-level="s"/panic="abort"/strip=true + override حزمي opt-level="z" — **لا مفتاح overflow-checks**؛ [profile.dev] = panic فقط (overflow-checks الافتراضي في dev يرتفع مع debug_assertions).
  - **لا `.cargo/`** في أي من الرأسين (`git ls-tree` فارغ لكليهما).
  - `git grep -inE "RUSTFLAGS|CARGO_PROFILE|overflow.checks" <rev>` على الشجرة كاملة: الإصابة الوحيدة `Makefile:5 CARGO_PROFILE_FLAG := $(if $(filter release,$(PROFILE)),--release,)` — متغير يحمل `--release` فقط، لا أعلامًا إضافية؛ لا RUSTFLAGS ولا CARGO_PROFILE_* بيئي في أي مكان.
  - لا `debug-assertions` في أي إعداد بناء (grep فارغ) — لا تفعيل ضمني عبر flip الـassertions في release.
  - `git diff fbe6472e origin/main -- Cargo.toml Makefile rust-toolchain.toml` = **فارغ** — الـ9 commits الجديدة (حتى دمج PR #41/Gate 20) لم تلمس إعداد البناء.
- **الشرط 2 — الـprofile الفعلي لبناء النواة [MEASURED]:** `Makefile:4 PROFILE ?= release` + `Makefile:94 cargo build --package ginux-kernel --target x86_64-unknown-uefi $(CARGO_PROFILE_FLAG)`؛ CI الوحيد `.github/workflows/check.yml` يشغّل `make check`/`make test`/`make test-qemu-smoke` بلا تجاوز PROFILE ⇒ **release هو الافتراضي محليًا وفي CI**، والأطروحة قائمة كما هي.
- **الشرط 1ب — لا نقاش سابق في dump [MEASURED]:** مسح كامل لـ"overflow" (scripts/grep_dump_overflow.py): 35 إصابة كلها غير ذات صلة — #16 stack overflow (عمق استدعاء)، PR #7 `checked_mul` موضعية + errno EOVERFLOW (كود لا سياسة)، PR #39 حقول overflow_count لطوابير إدخال محدودة، سلاسل اختبار runtime في boot.sh، وبقية إصابات وسوم KWMATCH الداخلية. **صفر إصابات لـ"overflow-checks" أو نقاش التفاف release** ⇒ لا إسقاط.
- **النص المعتمد (حرفي، EN، 90 كلمة):**
> Question on the build profile (AI-assisted review, under my direction): [profile.release] sets panic = "abort" but has no overflow-checks key, so, unless the build passes -C overflow-checks elsewhere, release builds wrap silently on integer overflow while debug builds panic. For size/length arithmetic derived from untrusted input (e.g. archive headers), wrapping would skip the check that panics in debug. Is this intentional? If not, enabling overflow-checks = true for release, measuring the boot-time/size cost, and adding one regression test on a wrapping size computation might be worth considering. Checked at main@fbe6472e.
- **الدليل:** `v2/artifacts/TA/cargo_profiles.txt` + تحققات 2026-11-02 أعلاه؛ نظام تحقق القارئ: `git show fbe6472e:Cargo.toml | grep overflow` (فارغ) و`git grep -i overflow-checks fbe6472e` (فارغ).

## C-2 — P15: مخاطر نمطية للشيفرة المولّدة آليًا (الخطورة: معلوماتية)
- ملاحظة عملية (23% من الأسطر مولّدة، إشراف اتجاهي لا سطري) وليست عيب كود محدد؛ **بلا مسودة علنية** — رأي يخص منهجية المشروع، يناقش فقط إن طلبت أنت ذلك.
- الدليل: `docs/paper/STEERING-PROVENANCE.md`؛ Critical 7.3.4.

## C-3 — P14: COW معطّل لمسار forks (الخطورة: منخفضة — دَين أداء معلن)
- قرار تصميمي يعلنه المستودع نفسه؛ اقتراح علني لن يضيف معلومة جديدة ⇒ **بلا مسودة** (أُسقط من المساهمات: مطروح ذاتيًا في وثائقهم).

## C-4/C-5 — P16 (فرق عدّ unsafe fn 108/110) وP17 (غياب خط الأساس في v1)
- منهجيتان داخليتان لتقييمنا، لا تعيبان Ginux ⇒ بلا مسودة؛ تُحفظان للأرشفة في docs/HISTORY.md عند الحاجة.

---
**الأمنية:** لا توجد مشاكل C من فئة "أمنية خاصة" في هذه الجولة — P10 صيغت كـrobustness لا كادعاء أمني (POLICY Tier-2 يظل مفعّلًا لأي نشر).

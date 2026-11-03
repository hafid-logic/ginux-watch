# قواعد المساهمة في ginx عند c86945b1 — تقرير Card T-20261103-06

المرجع: `gmkurtzer/ginux @ origin/main = c86945b1` (Merge PR #56). كل الاستشهادات بصيغة `ginux@c86945b1:<path>:<line>`. الشجرة في `work/ginux` تعديلاتها mode-only فقط (0 إضافات/0 حذوف، 256 ملفًا) [MEASURED: `git diff --stat`].

## 1) الترخيص License
- LICENSE = Apache License 2.0 [MEASURED: ginux@c86945b1:LICENSE:1-2]. NOTICE = "Ginux / Copyright 2026 Ginux contributors" [MEASURED: NOTICE:1-3].
- لا يوجد SPDX header ولا license header في ملفات .rs: أول سطر في `crates/oci/src/lib.rs:1` و`crates/protocol-state/src/lib.rs:1` و`crates/volume-format/src/lib.rs:1` هو `#![no_std]` [MEASURED]. `git grep SPDX-License-Identifier origin/main` لا يُرجع شيئًا، ولا ملف .rs يحتوي "Copyright" [MEASURED].
- Root `Cargo.toml:23` تحت `[workspace.package]`: `license = "Apache-2.0"`، وكل crate يستخدم `license.workspace = true` (مثل crates/oci/Cargo.toml:5) [MEASURED].
- **القاعدة لـ fuzz/**: بما أن fuzz/ سيكون workspace منفصلًا (خارج members)، يجب أن يعلن بنفسه `license = "Apache-2.0"` في Cargo.toml الخاص به، مع الالتزام بروح Apache-2.0/NOTICE [INFERRED من النمط المقاس].

## 2) سياسة الاعتماديات External dependencies
- لا يوجد `deny.toml` ولا cargo-deny ولا vendoring ولا `.cargo/config.toml` ولا `[patch]` في أي مكان (root + tools/) [MEASURED: ls-tree/grep بلا نتائج]. لا توجد قواعد عدّ اعتماديات dep-count [MEASURED: grep "dependenc" في Makefile/tools/docs بلا قواعد].
- النمط المؤكد: تثبيت دقيق بـ `=` في manifests: `heapless = "=0.9.2"`, `serde = "=1.0.228"`, `sha2 = "=0.11.0"` (crates/oci/Cargo.toml:11-14)، `ed25519-dalek = "=3.0.0"`, `smoltcp = "=0.14.0"` (kernel/Cargo.toml:14,19)، وكل الحزم `publish = false` [MEASURED]. Cargo.lock فيه 119 حزمة [MEASURED].
- **القاعدة**: اعتماديات fuzz/ (libfuzzer-sys/arbitrary...) يجب تثبيتها بـ `=` وقفلها في fuzz/Cargo.lock، ودون المساس بـ Cargo.lock الجذري [INFERRED].

## 3) هل تفحص root checks المجلدات الجديدة؟ (السؤال الحرج)
- `Makefile:239`: `check: manifest architecture-check linux-compat-check` ثم `cargo fmt --all -- --check` (:241) وقائمة clippy/test صريحة بالحزم (16 استدعاء `cargo clippy --package ...` في :242-265) [MEASURED].
- `cargo fmt --all` يعمل على أعضاء workspace الجذري فقط، و`Cargo.toml:2-21` يسرد 17 عضوًا صراحةً (لا fuzz/)؛ `cargo fmt --all` لا يدخل sub-workspace منفصل [MEASURED للقائمة + INFERRED لدلالات cargo]. **fuzz/ لن يُفحص fmt/clippy إطلاقًا**.
- `manifest` (Makefile:72): أهداف ثابتة + `cargo run --package ginux-manifest-tool --` بوسائط ثابتة تكتب `boot/efi/src/generated_boot.rs` — لا مسح شجرة [MEASURED].
- `architecture-check` (Makefile:230) → tools/architecture/check.sh: grep على ملفات معدودة (ARCHITECTURE.md، docs/ROADMAP.md، docs/decisions/0002، control-plane/runtime/src/main.rs) + 6 سكربتات فرعية كلها على مسارات معدودة، ما عدا `check-kernel-unsafe.sh` (rg على `kernel/src` فقط) و`inventory-writable-globals.sh` (`source_roots=(kernel control-plane services boot)`) [MEASURED]. fuzz/ خارج كل ذلك.
- `linux-compat-check` (Makefile:233): awk على docs/LINUX-COMPATIBILITY.md + kernel/src/arch/x86_64/cpu.rs [MEASURED]. `doctor` (Makefile:69 → tools/qemu/doctor.sh): فحص وجود cargo/rustc/clang/qemu وأجهزة QEMU/OVMF فقط، دون أي أمر cargo [MEASURED]. `test` (Makefile:219) = `build-verification` (:133، بناء ginux-boot فقط) + tests/qemu/boot.sh [MEASURED].
- **الخلاصة**: لا يوجد أي فحص جذر يمسح الشجرة كاملة (لا `rg/find/**` على الجذر). `make check`/`make test` آمنان ضد fuzz/ بشرط وحيد: **عدم إضافة "fuzz" إلى members الجذري** — وإلا سيمرّ fmt/clippy عليه بقناة stable 1.99.0 ويفشلان (cargo-fuzz يتطلب nightly) [INFERRED]. `gate` يضيف `git diff --check` (:276، مسافات بيضاء فقط) [MEASURED].

## 4) Toolchain
- root `rust-toolchain.toml`: channel = "1.99.0" (:2)، components = clippy+rustfmt (:4)، targets = ["x86_64-unknown-uefi"] فقط (:5) [MEASURED].
- لا يوجد أي ذكر لـ "nightly" أو "rust-toolchain" في أي .md/.toml [MEASURED: grep فارغ]. لا تعارض موثق مع fuzz/rust-toolchain.toml (nightly-2026-11-02)؛ rustup يحل الملف الأقرب لكل دليل، فيسري nightly داخل fuzz/ فقط [INFERRED].

## 5) أسلوب رسائل الالتزام Commit style
- `git log --oneline -30 origin/main`: مزيج من merge commits على GitHub ("Merge pull request #N from ...") والتزامات عمل: بعضها Conventional prefix صغير (`fix:` في 2c367116، `test:` في 586de64d) وأكثرها جملة imperative بلا prefix ("Enforce per-domain Linux memory limits" 013eaa1f، "Hide whiteouted directory subtrees" 344f4d84) [MEASURED].
- نمط HDAE متكرر: "Define <X> gate" → إصلاح → "Record <X> verification evidence" → "Link <X> delivery" [OBSERVED: 3013a1b0/013eaa1f/96310a8f]. الالتزامات المباشرة تحمل `Signed-off-by` (DCO) [MEASURED: log full c5280b44]. **التوصية**: PR بجملة imperative، ويُقبل `fix:`/`feat:`، مع دليل تحقق [INFERRED].

## 6) CI
- **تصحيح لفرضية البطاقة**: `.github/` موجود عند c86945b1 [MEASURED: ls-tree] ويضم workflow اثنين: `check.yml` و`issue-14-linux-repro.yml` [MEASURED].
- check.yml: job‏ `static` على ubuntu-24.04 ينفذ `make check`، وjob‏ `qemu` على macos-15-intel ينفذ `make test-qemu-smoke` عند PR و`make test` عند push؛ وكلاهما `rustup target add x86_64-unknown-uefi x86_64-unknown-none` [MEASURED: .github/workflows/check.yml].
- شذوذ في الـ blob: سطر `branches:` في check.yml يحرفيًا `ain]` والآخر `dae/issue-14-native-volume-linux]` (يفقد `[` الافتتاحية) [MEASURED: cat -A]؛ دلاليًا يعني أن trigger الـ push شبه معطّل، أما `pull_request:` بلا فلتر فيعمل على كل PR [INFERRED].
- لا توثيق لمتطلبات CI في README/docs غير ذلك (فقط "enforce coverage in CI" في docs/FEEDBACK-HARDENING-RESEARCH.md:76) [MEASURED].

## 7) AGENTS.md / CONTRIBUTING / .hdae
- AGENTS.md موجود في الجذر: يوجّه قراءة `.agents/skills/hdae-development/SKILL.md` بعد أي compaction/handoff [MEASURED: AGENTS.md:1-9]. لا يوجد CONTRIBUTING في أي مكان [MEASURED: grep exit=1].
- **`.hdae` موجود عند c86945b1** (VERSION، manifest، skills/hdae-development، skills/pr-issue-review) ولم يُزل: تاريخه 9802ae3d → 1852455e → fb8337bb تحديثات فقط [MEASURED: ls-tree -r + log -- .hdae]. فرضية "أزاله #56" غير صحيحة؛ #56 (c86945b1) لا يمس .hdae [MEASURED].
- يوجد أيضًا `.agents/` و`.claude/` (شجرتا skills) و`hdae/` (حالة المشروع) [MEASURED: ls-tree].

## قرارات PR (المدخل لـ 2e)
يجب على PR‏ fuzz/: license‏ Apache-2.0 ذاتي الإعلان؛ تثبيت deps بـ `=`؛ workspace منفصل خارج members الجذري؛ rust-toolchain محلي مقبول؛ رسالة imperative؛ لا حاجة لتعديل Makefile حتى يعمل `make check`/`make test` — لكنه في المقابل **لن يُبنى أو يُختبر في CI الغرباء إطلاقًا** (لا workflow ولا target يستدعيه)، ما يجعل إضافة workflow/Makefile target اختياريًا قرارًا مفتوحًا للمشرف [INFERRED]. شذوذات: .github موجود عكس فرضية البطاقة، وفلتر branches تالف في check.yml، و.gitignore الجذري لا يغطي fuzz/target أو fuzz/artifacts (سيضيف PR حاجته الخاصة) [MEASURED: .gitignore:1-5].

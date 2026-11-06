# مسودة v2 — فرصة 2: استعادة `overflow-checks` في `[profile.release]` (توجيه v4.2 §5)
الحالة: **غير منشور — لا يُنشر إلا باعتماد المستخدم الحرفي.** تلغي v1 (drafts/2026-11-05-overflow-checks-draft.md) وتحتفظ بنصها كما أُرسل حرفيًا. **تحديث 2026-11-06 (v4.3): المستخدم اعتمد نصًا نهائيًا معدلًا لهذا المسودة → محفوظ حرفيًا في approved/2026-11-06-1.md؛ هذا الملف يبقى سجل الأدلة ولا يُنشر.**

---

## النص المقترح (كما أُرسل — بلا تغيير حرف واحد)

Title: `restore overflow-checks in release profile (lost in userspace pivot)`

Body (≤120 كلمة):
> During the standalone-kernel phase, `overflow-checks = true` was enabled in
> `[profile.release]` to make integer-overflow behavior deterministic in
> supervisor paths that validate untrusted input (see #43, #54). The current
> `[profile.release]` in the userspace tree no longer sets it, so release
> builds silently wrap on overflow again. The supervisor parses attacker-
> controlled structures (tar/PAX headers, volumes, configs) where a wrapping
> offset can turn into an out-of-bounds read/write downstream. Proposed
> one-line change:
>
> ```toml
> [profile.release]
> overflow-checks = true
> ```
>
> No benchmark has been run for this tree yet; happy to provide one for the
> parsing crates before merge, or send the change as a PR if preferred.

---

## إضافات v2 — الدليل الحي @64a3e3f7 (توجيه v4.2 §2–3؛ «السهم» المكتمل)

### أ) الحذف مثبت (الادعاء «lost» في العنوان صحيح)
- أُضيفت بـ`9b11baea` «Enable release overflow checks» — أول commit في فرع PR #54 (`gmkurtzer/hdae/issue-43-release-overflow`، إصلاح المالك لتحليلنا #43؛ تذييلات المالك: a3f0c33d/50e06d76/66648d28/a0e9220b/47fc22c8)؛ المدموجة كـ`6324692b` في 2026-11-03T22:00:12Z [MEASURED].
- حُذفت **داخل دمج `d337713b` (#152 userspace-transition، 2026-11-04T18:15:51−05:00)** — لا commit حذف مستقل (`d337713b^1` يحمل السطر؛ `^2` والنتيجة لا) [MEASURED].

### ب) `[profile.release]` الحالي @64a3e3f7 — حرفيًا [MEASURED]
```toml
[profile.release]
codegen-units = 1
lto = true
opt-level = "s"
panic = "abort"
strip = true
```

### ج) المواقع الحسابية غير المفحوصة على أطوال/إزاحات مشتقة من الترويسات (9 مواقع + صفر `<<`) [MEASURED مواقع، INFERRED قابلية الوصول]
| # | الموقع file:line | العملية | القيمة المشتقة | تقييم الحدود [INFERRED] |
|---|---|---|---|---|
| 1 | ginux-vfs-index/src/main.rs:426 | `offset + 512` | ترويسة tar التالية | ≤ source_len (حجم الملف) — لا إغراق عمليًا |
| 2 | …main.rs:436 | `offset + 512` | data_offset | نفس 1 |
| 3 | …main.rs:437 | `… / 512 * 512` | padded | (x/512)*512 ≤ x — لا إغراق؛ **الجمع checked_add(511) محصّن** |
| 4 | …main.rs:347 | `slash + 1` | اسم whiteout | < path.len() (حد تخصيص) |
| 5 | …main.rs:680 | `position + offset` | طول سجل PAX | ≤ 2×len ≤ isize::MAX×2 — لا إغراق |
| 6 | …main.rs:683 | `space + 2` | نفس 5 | bound كـ5 |
| 7 | …main.rs:686 | `space + 1` | نص السجل | bound كـ5 |
| 8 | …main.rs:691 | `equals + 1` | مفتاح=قيمة | < record.len() |
| 9 | …main.rs:633 | `path.len() + 1` | path ترويسة/PAX | ≤ isize::MAX (حد تخصيص) |

محصّنة مسبقًا (checked_add موجود): main.rs:437 (الجمع)، 439 (`end = data_offset+padded`)، 682 (`PAX length overflow`). `parse_octal` ترجع Err على الفيض بـfrom_str_radix؛ checksum sum bounded (512×255).
⇒ **السهم:** التفعيل يحول أي إغراق مستقبلي جديد في هذه المنطقة من صمت إلى panic فاشل-بأمان (نمط F5/fail-closed)؛ اليوم لا إغراق حي [INFERRED].

### د) البناء والاختبار محليًا @64a3e3f7 بـ`CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS=true` [MEASURED]
- النتيجة: **نجاح؛ 65/65 اختبار وحدة تمر** (core 8/domain 11/devices 6/runtime 10/process 12/vfs 12/kernel-views 6) — نفس وصفة Makefile test-unit (RUSTFLAGS='') مع فلاغ البيئة.
- probe استقلالي يثبت فعالية الفلاغ: u8 250+10 ⇒ يلغف صامتًا إلى 4 بلا فلاغ، panic «attempt to add with overflow» معه.
- **الحجم: `ginux-vfs-index` = 361,320 بايت في الحالتين (baseline = with-flag، مطابق)** ⇒ التفعيل بلا كلفة حجمية على مرساة المParser.
- انحراف بيئة الصندوق (ليس فشل فلاغ): لا rust-lld في توزيعة dist-tarball ولا sudo ⇒ الثنائيات self-start (ginux، runtime-fixture، baseline-runner، process-native-fixture) لا تُبنى محليًا (تصميمها rocky-host/Actions: `-C linker=rust-lld -nostdlib -static`)؛ بقية المكتبات + ginux-vfs-index بنيت بديلًا ديناميكيًا (cc+bfd، `link-self-contained=no`) — النتيجة الدلالية للـoverflow-checks غير متأثرة.
- Toolchain محلي: rust 1.99.1 stable (dist tarball، sysroot مُرمم يدويًا).

## ملاحظات النشر (بلا تغيير عن v1)
- قبل النشر: تأكد أن #54/#43 لا تزال تشير للأصل، وأن أحدًا لم يقدم نفس التغيير.
- النسخة الأنسب: PR صغير (+1/−0) مع الإشارة إلى #43/#54.
- **لا نشر بلا قرارك الحرفي** (POLICY 0–3).

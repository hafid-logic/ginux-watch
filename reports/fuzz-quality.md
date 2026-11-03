# جودة الـ fuzz قبل أي تشغيل جديد — v2.6-1 [MEASURED 2026-11-03]

القياس: `cargo fuzz coverage` 0.13.2 + llvm-cov على **seeds فقط** (53 ملفًا جديدًا في
`fuzz/corpus-seed/`) مقابل crate الـ upstream الحقيقي عند pin `82df3d71` (path-dep، بلا
إعادة كتابة). لا ASan في بناء coverage (سلوك الأداة الطبيعي). عمود Branches في llvm-cov
فارغ (البناء بلا `-Zcoverage-options=branch`)؛ المقاييس: regions/functions/lines + قوائم
الدوال الاسمية. المصدر: `fuzz/coverage/oci_surfaces/coverage.profdata`.

## a) تغطية الـ harness لدوال PAX/tar/gzip الفعلية

- إجمالي `upstream/crates/oci/src/lib.rs` (1238 سطرًا): **66.27% regions** (287/851
  missed) / **65.98% functions** (33/97) / **68.06% lines** (214/670).
- **الفجوة الأكبر — طبقة الاستعلام/الاستعراض كلها 0%** (33 دالة): `Rootfs::{find,
  find_index, find_indexed, entry, entry_indexed, entry_at_offset,
  entry_and_next_at_offset, next_child, copy_path, from_metadata, metadata,
  content_length}` + `RootfsMetadata::{new, entry_count, content_length}` +
  `whiteout_hides` / `copy_entry_path` / `entry_path_matches`. النواة نفسها تستدعي هذه
  الطبقة بمدخلات الطبقات (`kernel/src/published_rootfs.rs@82df3d71`: `metadata()`,
  `entry_count()`, `entry_and_next_at_offset` سطر 207، `entry_at_offset` سطرا 267/392/471،
  `find_index` سطر 407) ⇒ الـ harness الحالي (v2.5) لا يطابق سطح الاستخدام الفعلي في
  النواة لهذه الطبقة — يستدعي `parse` فقط.
- محللات tar/PAX نفسها **جزئية حتى مع seeds صالحة**: `parse_entry` 80.42% (28/143
  regions)، `parse_pax_overrides` 82.86% (6/35)، `Rootfs::parse` 86.11% (5/36)، `octal`
  85.71% (3/21)، `stored_checksum` 83.33%.
- سطوح registry جزئية: `parse_sha256_selector` 73.91%، `hex_nibble` 71.43%،
  `platform_matches` 71.43% (فروع variant)، `BearerChallenge::parse` 76.92%،
  `ImageReference::parse` 94.64% (3/56).
- **gzip: لا يوجد محلل في `crates/oci` إطلاقًا** (نص media-type فقط
  `tar+gzip`) — محلل gzip في `kernel/src/image_store.rs` داخل crate غير قابل للاختبار
  على المضيف (نفس منطق D12) ⇒ لا يُقاس هنا ولا harness له بتكلفة منخفضة.

## b) overflow-checks / حدود الحجم الحقيقية / ASan

- [MEASURED] أعلام البناء الفعلية (`cargo fuzz build -v`): profile `release` + 
  `-Cdebug-assertions` + `-Zsanitizer=address` (ASan) + sancov كامل (level 4,
  trace-compares, pc-table, inline-8bit-counters) + `-Ccodegen-units=1`.
- [MEASURED probe] `-Cdebug-assertions` يفعّل overflow-checks ضمنيًا في rustc (مسبقة
  runtime: `0usize-1` ⇒ panic مع العلم؛ التفاف صامت بدونه) ⇒ الـ harness
  **overflow-checks=true** — يطابق وأشد من release+#54 (الذي أضاف
  `[profile.release] overflow-checks = true` [MEASURED من diff #54]).
- [VERIFIED] `debug_assert!/unwrap/expect` = **صفر** في كود الـ crate قبل الاختبارات
  (أول `mod tests` سطر 977) ⇒ فئات panic في الـ harness ≡ release+#54 لهذا الـ crate.
- [VERIFIED] حدود الحجم الحقيقية داخل الـ crate نفسه (`TAR_MAX_ENTRIES=32768`,
  `OCI_LAYER_LIMIT=16`, `REFERENCE_CAPACITY=128`, سعات heapless) — لا
  reimplementation في الـ harness؛ الـ entry points نفسها التي تستدعيها النواة.

## c) حالة corpus قبل الإصلاح

- [MEASURED] **غير مبذور**: CI ينشئ `fuzz/corpus` على checkout نظيف = فارغ؛ corpus
  جولة v2.5 لم يُحفظ (رفع artifacts مشروط بالفشل)؛ المحلي فُقد بإعادة تدوير sandbox ⇒
  الـ 106,140,505 execs في v2.5 بدأت من صفر seeds.
- الإصلاح (v2.6-2): `fuzz/corpus-seed/` ملتزم (53: أرشيفات صالحة من اختبارات الـ
  crate عند الـ pin + حدودية: حجم 0، 512 بالضبط، 513، 2^32 = `0o40000000000`، أقصى
  `0o77777777777`، prefix+name بحدّي 100/155، whiteout/opaque، سلاسل PAX تكرارية
  بعد 4294c0a7) + `fuzz/oci.dict` (حقول حدية: `ustar\0`, `path=`, `linkpath=`, `.wh.`,
  `sha256:`, أنواع media، مفاتيح JSON).

## d) محللات أخرى تقبل مدخلات غير موثوقة — مرتبة بالخطر (تعرض × تحكم مهاجم × قابلية استهداف)

1. `crates/protocol-state` — `parse_arp_reply_v4` / `parse_ipv4_icmp_v0` /
   `parse_icmp_echo_request_v0`: بايتات شبكة خام (أبعد سطح هجوم؛ قبل TLS)؛ دوال نقية
   على `&[u8]`؛ crate مضيف ⇒ **harness منخفض التكلفة** (مرشح v2.6-4).
2. `crates/volume-format` — `Header::decode` / `Record::decode`: محتوى قطاعات volume
   (مهاجم = قرص)؛ نقية ⇒ منخفض التكلفة.
3. `crates/oci-cache` — `Cache::decode(input: &[u8])`: ملف cache (مهاجم لو سُمّم) ⇒ منخفض.
4. `crates/command` — `parse`: مدخلات control-plane محلية شبه موثوقة ⇒ متوسط.
5. `crates/image-store` — `read(digest, offset, …)`: digest-addressed وoffset مُتحقق ⇒ متوسط-منخفض.
6. `services/network/src/registry.rs` (1802 سطرًا) — HTTP/registry بعيد غير موثوق لكنه
   **binary** (`main.rs`) بلا lib crate ⇒ يتطلب إعادة هيكلة ⇒ **ليس تكلفة منخفضة**
   (يُستبعد من v2.6-4 بهذا السبب الموثق).

المصادر: llvm-cov/profdata أعلاه؛ `cargo fuzz build -v`؛
`upstream/kernel/src/published_rootfs.rs@82df3d71`؛ diff PR #54 (C Cargo.toml +
regression test في crates/oci).

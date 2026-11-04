# T-20261104-07 — جدوى هدف fuzz رابع (TCP/DNS/PAX) على main@7fdc880e [MEASURED]

السؤال (v3.1 §1): هل أضافت موجة الدمج الأخيرة (TCP، DNS، PAX الجديد وما بعده) محلّلات
 جديدة تقبل مدخلات غير موثوقة تبرر هدفًا رابعًا؟ الجدوى فقط: قابل للتشغيل على المضيف؟

## الخلاصة: لا هدف رابع مبرَّر الآن — صفر محلّلات جديدة مملوكة للمستودع

- **PAX/tar:** `crates/oci/src/lib.rs:512` `Rootfs::parse(&[u8])`، `:756` `parse_entry`،
  `:855` `parse_pax_overrides` — دوال نقية على `&[u8]` والـcrate قابل للبناء على المضيف.
  **مغطى أصلًا** بالهدف الأول `fuzz/fuzz_targets/oci_surfaces.rs:33-124` (يرسم سلسلة
  استدعاء النواة: `from_metadata`/`entry_at_offset`/`next_child`) وببذور pax t05–t08؛
  تقسية PAX التكرارية من `4294c0a7` مُمارَسة [تأكيدها: تغطية oci 93.18% regions في
  جولة v3.1 على 7fdc880e]. ملاحظة: `kernel/src/initramfs.rs:74` محلّل **cpio-newc**
  (لا tar/PAX) وهو `pub(crate)` داخل نواة `#![no_std]` — لا يُبلغ منه على المضيف؛
  و`crates/volume-format` بلا أي tar/PAX (فقط `Record::decode`/`HostVolumeHeader::decode`).
- **TCP:** لا محلّل wire مملوك للمستودع — التحليل في **smoltcp 0.14.0** الخارجي
  (kernel/Cargo.toml:26؛ import في kernel/src/linux_socket.rs:4-13). commits الموجة
  (`eb931ced` accept paths +79، `e063ad37` queue connections +40) لمسوا حالة
  `linux_socket.rs` فقط (فحص backlog :544، `backlog: u8` :115) فوق كائنات
  `tcp::Socket` الجاهزة. النواة `#![no_std]` + global_asm + virtio-NIC ⇒ لا
  host-runnable (يحتاج QEMU). وfuzz لـsmoltcp = fuzz لتبعية upstream لا لكود ginux.
- **DNS:** لا محلّل رسائل DNS مملوك — عبر smoltcp `socket::dns` في
  services/network/src/registry.rs:28-30,132 (`DnsSocket::new`؛ PR #73 `5dd58ca4` ربط
  socket/entropy فقط، +143). `dns_name_matches` (:885) مطابقة نصوص TLS-SAN لا wire.
- **المحلّل الوحيد المملوك على wire:** `unsafe fn parse_dhcp_reply`
  (services/network/src/main.rs:643، مؤشرات خام) — لكن الـcrate خدمة
  `#![no_std] #![no_main]` ⇒ غير قابل للتشغيل على المضيف حاليًا، وهو DHCP لا DNS.
  **مرشّح مستقبلي وحيد** إن استُخرج إلى crate مستقلة std (قرار جديد — انظر
  drafts/2026-11-04-next-contributions.md فكرة 2).

## خريطة نافذة الدمج
PAX → `4294c0a7` (قبل النافذة، خط #43/#61) | DNS → #73 `5dd58ca4` | TCP
accept/queue → `eb931ced`/`e063ad37` (قبل النافذة) | #81 (mmap access) و#84
(scheduler atomicity) و#86 (overlay accounting: kernel/lib.rs + linux_overlay.rs)
لم تلمس أي محلّل. أهداف fuzz نفسها من #61 (`47ff7107`).

القرار: إبقاء الأهداف الثلاثة كما هي؛ إعادة التشغيل الدوري كافية. أي تحوّل لاحق
 (استخراج DHCP إلى crate) يفتح باب هدف رابع — يُعاد التقييم حينها فقط.

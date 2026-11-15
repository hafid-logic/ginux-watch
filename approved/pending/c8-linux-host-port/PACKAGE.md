# PACKAGE — C-8: Linux portability for the Rocky host flow

id: c8-linux-host-port | branch: `c8/linux-host-port` (ginux-watch) | status: PENDING-SUPERVISOR
directive: v8.1-1 | prepared: 2026-11-15 (session s66)

## (أ) القاعدة والفرق وإعادة الإنتاج

- upstream main وقت التجهيز: `285d025b7f8bcad0784585dcfbd23cada4643408` (committer date 2026-11-13T21:30:14-08:00 = 2026-11-14T05:30:14Z) [MEASURED API + git]
- فرعنا الرقعي: commit `9f04011b` محلياً فوق 285d025b؛ النقل إلى فرع ginux-watch `c8/linux-host-port` كملف `patches/linux-host-port.patch` (format-patch واحد، sha256 بالأسفل)
- الفرق: 3 ملفات، +46/−12 — `scripts/prepare-rocky-host.sh` (+34/−10)، `scripts/doctor.sh` (+19/−1)، `scripts/verify-rocky-host.sh` (+5/−1)
- طبيعة التغيير: تفريع أدوات macOS فقط عند غياب Darwin — `hdiutil makehybrid` → `xorriso -as mkisofs` أو `genisoimage` (وسم حجم `cidata` + Joliet + Rock Ridge) لبناء قرص cloud-init؛ `shasum -a 256` → `sha256sum`؛ doctor: قائمة أدوات لكل OS + قبول Linux x86_64 كـreference host. **مسار Darwin حرفياً كما هو** (نفس الأوامر داخل case Darwin)، و`start-rocky-host.sh` نفسه بلا تعديل (lsof اختياري فيه وqemu/ssh محمولة أصلاً).
- sha256 لملف الرقعة: (يُبلَّغ بعد الcommit النهائي في هذا الملف نفسه)
- أوامر إعادة الإنتاج:
  1. `git -C work/upstream-ginux fetch origin main && git -C work/upstream-ginux checkout -B port-recheck FETCH_HEAD && git -C work/upstream-ginux apply --3way work/ginux-watch/patches/linux-host-port.patch`
  2. تشغيل الاختبار: `cd work/upstream-ginux && sudo apt-get install -y xorriso qemu-system-x86 qemu-utils && make host-image-fetch && ./scripts/start-rocky-host.sh && ./scripts/check-rocky-host.sh`

## (ب) روابط تشغيلات Actions (على 285d025b، runner ubuntu-24.04)

| # | الغرض | الرابط | النتيجة |
|---|---|---|---|
| 1 | إقلاع Rocky VM على Linux (فشل-ثم-نجاح موثق في نفس الrun) | TBA-BOOT | TBA |
| 2 | بوابة واحدة: `make test-contract` + doctor مرقّع | TBA-GATE-1 | TBA |
| 3 | تشغيل ثانٍ للبوابة (إثبات التكرار) | TBA-GATE-2 | TBA |

(تُستبدل TBA بروابط حقيقية بعد التشغيل قبل تسليم الحزمة للمشرف — لا اعتماد بروابط ناقصة.)

## (ج) فحص التعارض [MEASURED git على 2026-11-15T10:4xZ]

- PRs المفتوحة (2): #292 (733ff943، security/allocator — 50 ملفاً) و#291 (c4609fbe، Gate 31 — 21 ملفاً). تقاطع ملفات #292/#291 مع ملفاتنا الثلاثة = **صفر** (فحص rg على قائمتي الملفات الكاملتين، rc=1).
- PRs مدموجة منذ SHA الأساس: الأساس = رأس main الحي نفسه ⇒ صفر دمجات بعده وقت التجهيز. آخر 40 دمجة خلفه لا تلمس ملفاتنا (لا doctor.sh ولا prepare-rocky-host.sh ولا verify-rocky-host.sh).
- استبعاد التكرار: لا PR مفتوحاً أو مدمجاً حديثاً يعالج قابلية نقل Linux للhost flow (بحث العناوين + الملفات أعلاه) — الفرصة قائمة.

## (د) التعليل (≤ 8 أسطر) والمخاطر ونص النشر المقترح

- سلسلة start→prepare→verify كانت تفشل على Linux عند أول أداة macOS: hdiutil غائب [MEASURED: command -v hdiutil فشل على runner موثق في run 1] — الرقعة تفرد المسار دون لمس Darwin.
- تعارض صفر (ج) + الأساس = رأس main الحي ⇒ فرع طازج وفق قاعدة قبول 6 (maintainer-profile).
- CI الupstream يجري على ubuntu-24.04 وmacos-15-intel — ساق Linux صارت مغطاة بdoctor مرقّع [MEASURED: run 2].
- المخاطر: **غير حساس** — سكربتات بناء/تحقق فقط، لا كود نواة، لا سطح أمني، لا تغيير سلوك macOS (مسار Darwin حرفي).
- نص النشر المقترح (PR body، ≤120 كلمة، إنجليزي، إفصاح AI):

```
The Rocky host flow (scripts/start-rocky-host.sh) assumes a macOS host: the
cloud-init seed is built with hdiutil, the image checksum uses shasum, and
doctor.sh accepts only Darwin-arm64 as the reference host.

Branch exactly those macOS-only tools and keep Darwin behavior unchanged:

- prepare-rocky-host.sh: build the cidata seed ISO with xorriso -as mkisofs
  (or genisoimage) on non-Darwin; hdiutil and the .cdr fallback untouched.
- verify-rocky-host.sh: sha256sum replaces shasum off Darwin.
- doctor.sh: per-OS host tool list; Linux x86_64 accepted next to macOS arm64.

Verified on ubuntu-24.04: unpatched doctor and seed build fail at hdiutil,
patched doctor passes, Rocky 10 VM boots to SSH (TCG) with cloud-init ready,
and make test-contract passes (evidence runs linked below).

Analysis assisted by AI, reviewed by Abdelhafid DJIDEL.
```

## (هـ) أمر واحد يُنتج الفرق على أحدث main

```sh
git -C work/upstream-ginux fetch origin main && git -C work/upstream-ginux checkout -B port-recheck FETCH_HEAD && git -C work/upstream-ginux apply --3way work/ginux-watch/patches/linux-host-port.patch && git -C work/upstream-ginux diff HEAD --stat
```

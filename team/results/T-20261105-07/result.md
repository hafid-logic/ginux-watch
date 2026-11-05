# T-20261105-07 — أرشفة PR-A (archive-pra-package) — W2/builder

**الحالة:** done — الحزمة في `archive/pr-a-protocol-state-tests/` (4 ملفات) + هذه البطاقة و`meta.json`. لا git commit/push (الـ supervisor ي-push).

**1) التحقق من الـ patch [MEASURED]:** في `/home/z/my-project/work/ginux` (fork hafid-logic/ginux، فرع `feature/tests-protocol-state`) أعطى `git diff 4d4a53bb..c9f52308 -- crates/protocol-state/src/lib.rs | sha256sum` القيمة `62b7dd4bf7918f17796cf80418ad78642da36284af474752461e334ce977f0a3`، و`sha256sum reports/2026-11-05-pra-diff.patch` أعطى **نفس القيمة حرفيًا — تطابق تام، لا errata لهذه الخطوة**. النسخة إلى `archive/pr-a-protocol-state-tests/pr-a-2026-11-05.patch` أعيد فحصها: SHA مطابق، و`git diff --stat` يؤكد +71/−0 في ملف واحد `crates/protocol-state/src/lib.rs`.

**2) الملفات المنشأة (أحجام بالكلمات، wc -w) [MEASURED]:**
- `archive/pr-a-protocol-state-tests/README.md` — إنجليزي، **97 كلمة** (الحد ≤120): ما هي (اختبارات C1+C2، الفرع، الرأس `c9f52308`، draft PR fork#2)، لماذا لم تُرسل (freeze `cdf8038e`، cutoff 2026-11-05T07:59Z، قرار النشر لم يُتخذ)، وكيفية إعادة الاستخدام.
- `archive/pr-a-protocol-state-tests/pr-description.md` — نص الـ PR **حرفيًا** من `reports/2026-11-05.md` §2 (bullet «Pure unit tests only…»): **99 كلمة** (الحد ≤150).
- `archive/pr-a-protocol-state-tests/mutants-before-after.md` — جدول runs + صف check/test + سطر errata واحد.
- `archive/pr-a-protocol-state-tests/pr-a-2026-11-05.patch` — نسخة الـ patch (لا تعديل على `reports/`).

**3) الأدلة المُوثّقة في الجدول [MEASURED]:** mutants قبل — run [41905986161](https://github.com/hafid-logic/ginux-watch/actions/runs/41905986161) على main@`4d4a53bb`: 83 mutants، caught=55، missed=20 (checksum 5، ARP 5، ipv4 9، echo 1)؛ بعد — run [41916256214](https://github.com/hafid-logic/ginux-watch/actions/runs/41916256214) على `c9f52308`: caught=65، missed=10 (checksum=0، ARP=0، ipv4 9، echo 1)؛ الوسيط run [41915470999](https://github.com/hafid-logic/ginux-watch/actions/runs/41915470999) على `2b4e119e` بنفس missed=10. check/test — run [41916249282](https://github.com/hafid-logic/ginux-watch/actions/runs/41916249282): doctor=0 check=0 test=0 على QEMU 10.0.13 و10.1.2 مع 13/13 unit tests. المصدر: `reports/2026-11-05.md` §2.

**4) errata الوحيدة [MEASURED]:** run [41915447820](https://github.com/hafid-logic/ginux-watch/actions/runs/41915447820) (المحاولة الأولى على `2b4e119e`) فشل في `cargo fmt --check` على 3 أسطر طويلة — صُحح في `c9f52308`؛ doctor/test كانا 0/0 حتى عنده.

**5) الحدود:** draft PR في fork فقط hafid-logic/ginux#2 (draft=true)؛ لا شيء أُرسل upstream؛ لم يُعدَّل أي مسار خارج `archive/pr-a-protocol-state-tests/**` و`team/results/T-20261105-07/**`؛ لا أسرار في أي ملف.

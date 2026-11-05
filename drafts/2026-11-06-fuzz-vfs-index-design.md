# مسودة تصميم — fuzz retarget إلى ginux-vfs-index (فرصة 3، توجيه v4.1 §4)
الحالة: **تصميم فقط — لا تشغيل، لا workflow، لا PR.** تنفيذها بعد قرار المستخدم، والبدء موقوف 7 أيام (انظر §7).
الأساس الحي: upstream/main @ `64a3e3f7` (2026-11-05T23:27:08Z) — أرقام الأسطر أدناه أُعيد قياسها اليوم ولم تتحرك.

## 1) الأهداف (3 harnesses على `crates/ginux-vfs-index/src/main.rs`)
| الهدف | الدالة | السطر @64a3e3f7 | المدخل | لماذا |
|---|---|---|---|---|
| F1 | `scan_tar` | 414 | بايتات tar (ustar/GNU) | حلّل رؤوس غير موثوقة: أسماء، أحجام، sparse |
| F2 | `parse_pax` | 672 | PAX extended headers | بناء `PaxRecords` من مدخل عدائي |
| F3 | `whiteout` | 344 | `LayerRecord` | منطق طبقات/whiteout يحدد مسارات الإخراج |

ملاحظة جدوى (فرصة 1، الجدول في التقرير): vfs-index ثنائي نقي (unsafe ظاهري واحد = سلسلة رسالة خطأ في السطر 631، صفر FFI؛ deps الوحيدة = ginux-vfs الداخلية) ⇒ harnesses ممكنة داخل مستودعنا بمحاكاة الاستدعاء (extract-harness) دون تعديل upstream.

## 2) المدة (مقيدة، تُسجَّل قبل التنفيذ وفق نص البوابة §5)
- جولة تأسيسية: 30 دقيقة/هدف × 3 = 90 دقيقة إجمالًا (workflow_dispatch يدوي فقط — لا cron).
- جولات لاحقة: 30 دقيقة/هدف، سقف 90 دقيقة/أسبوع، تُسجل في reports/fuzz-history.md.

## 3) سقف الموارد (لكل هدف)
`-rss_limit_mb=2560 -malloc_limit_mb=2048 -timeout=25 -max_len=1048576 -fork=1 -ignore_crashes=0`؛
`-max_total_time=1800` يوقف الجولة حتمًا. artifacts (crash/hang/leak) تُرفع كـ artifact داخلي في ginux-watch لمدة 30 يومًا.

## 4) البذور (corpus قابل لإعادة الإنتاج)
لا توجد fixtures tar في upstream (tests/fixtures = C/S/toml فقط [MEASURED]) ⇒ بذور مبنية يدويًا في `fuzz/seeds/vfs-index/`:
ustar صغير (ملف واحد)؛ GNU longname؛ PAX بـ path/size/linkpath؛ PAX مع espaced تالف عمدًا؛ LayerRecord مع whiteout صحيح؛ LayerRecord بأسماء `..` ومطلقة. كل بذرة ≤1KB وبها SHA256 في manifest.

## 5) معالجة الأعطال
crash/hang ⇒ تقليل (minimize) يدوي + حفظ POC في `inbox/evidence/fuzz/` + إدخال في reports/fuzz-history.md؛ **لا PR ولا issue upstream** أثناء موجة meleficarumvaldis؛ الإبلاغ (سؤال/PR بنص معتمد في approved/) بعد قرار المستخدم فقط (POLICY 0–3).

## 6) معيار البوابة 13 المخدوم (حرفيًا من hdae/gates-todo/13-boundary-hardening.md @2489517e)
- النطاق المعتمد سطر 18–19: «Add bounded fuzz targets for security-critical parsers and dispatchers with reproducible seed corpora and crash-artifact handling.» ⇒ **داخل النطاق المعتمد** (tar/PAX محللات مدخلات غير موثوقة).
- معيار قبول سطر 54–58: تغطية كل parser أمني، و«Bounded fuzz runs complete for the approved duration and corpus without an untriaged crash, hang, memory-safety failure, or invariant violation.»
- Decisions سطر ~99: «Fuzz duration, target list, and resource ceiling are recorded before this gate executes» ⇒ هذه المسودة هي ذلك التسجيل.
- ملاحظة إجرائية: تسليم البوابة رسميًا عبر فرعهم `hdae/boundary-hardening` (سطر Delivery) — عملنا داخلي في ginux-watch ويُقدَّم لهم لاحقًا كبلاغ/PR بنص معتمد.

## 7) قرار تأخير 7 أيام (من v4.0 §5.4): **محتفظ به — مبرر بقياس حي**
المنطقة نشطة اليوم نفسه: بعد 21e48f7c دُمج #215 (melefi، 23:19Z) و3 دمجات vfs من veighnsche/LevitateOS: #216 «open fails» 23:21Z، #217 «unlink lifetime» 23:26Z، #218 «path resolution» 23:27Z [MEASURED]. vfs-index نفسها دُمجت عليها 3 PRs سابقة (#167/#175/#193). إعادة تقييم التأخير: **2026-11-12** (يتطابق مع مراجعة cron اليومية 507000).

# ملخص موحّد للمشرف — v8.8-B + v8.9 (2026-11-23)
يربط كل حزمة بدليلها الحيّ على عدّاء نظيف (ubuntu-24.04). **لا نشر في upstream**؛ بوابة النشر للمشغّل.

## جدول الربط: حزمة ↔ فرع/sha ↔ PR ↔ دليل ↔ حكم
| الحزمة | الفرع / الرأس | PR | الدليل الحيّ | الحكم |
|---|---|---|---|---|
| C-8 allocator c_char cfg | pkg/allocator-c-char-cfg @ 74abc984 | #58 | run 45242249906 · artifact e0425-evidence | عيب حقيقي [أ]: فشل exit=101 E0425 بأمر CI الحرفي ← إصلاح cfg أدنى ← نجاح |
| C-8 descriptors property tests | pkg/descriptors-property-tests @ 5d57db0d | #59 | run 45250026700 · artifact descriptors-mutants-evidence | طفرات m2/m5/m11 تنجو من الطقم الحالي (exit 0) وتُقتل باختباراتنا (exit 101)؛ baseline+سليم ناجح |
| ginux-oci reference-guards (مرجع معتمد غير منشور) | pkg/ginux-oci-reference-guards @ 26f6fa01 · PR.patch sha256 109acd94… | نشر المشغّل | مرجع مثبّت في STATE «حزم معتمدة غير منشورة» | معتمد من المشرف، ينتظر نشر المشغّل |

## بدائل مصنّفة
- patches/oci-property-tests.patch = **بديل غير معتمد** (اختبار human_size يثبّت تنسيق تقدّم؛ قيمة ضعيفة). ليس حزمة النشر.

## حوكمة (v8.9)
- #57: STATE قسم «حزم معتمدة غير منشورة» + قاعدة AGENTS «اقرأ القسم وapproved/pending قبل البناء؛ لا تعِد بناء الموجود؛ جاهز=مدفوع (فرع+sha)».

## ملاحظات فنية
- allocator: الاستيراد use core::ffi::c_char; مشروط not(test) بينما read_small_file (linux، يُترجم تحت test) يستخدم c_char (سطر 242) ⇒ E0425 على Linux. CI المالك (macos-15-intel) لا يمر بالمسار ⇒ يحجب العيب. الإصلاح: #[cfg(any(not(test), target_os = "linux"))].
- descriptors: طفرات سطر واحد (تعطيل فحص علم fd؛ close no-op؛ close بفهرس غير مقنّع) غير مغطاة بالطقم الحالي؛ اختبارات Property ترفض الفهرس الخام وتُبطل close وتحرّر الخانة ⇒ قتل مؤكد.

## حالة النشر
كل الحزم مدفوعة (فرع+sha) وجاهزة؛ النشر في upstream محجوب بانتظار المشغّل. PRات #57/#58/#59 لدمج المالك (المسارات المحمية human-only).

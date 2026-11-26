# DECISION — c8-property-tests-process-table

status: PENDING (بانتظار تحقق المشرف الحي ثم اعتماد المالك)

## ما يتحقق منه المشرف قبل الاعتماد (C-8)
1. مطابقة رأس الفرع `exp/property-tests-process-table` = `0709c41` وأن `property-tests/` فيه مطابق لما جرى في runs الطفرات (ref `exp/pt-mutants-scratch` — الفرق بينهما workflow الطفرات وملفات الرقع فقط [MEASURED]).
2. قراءة `property-tests/tests/process_table_properties.rs` والموديل مقابل `crates/ginux-process/src/lib.rs` @ 285d025b.
3. التحقق من نتائج runs الأربعة في (ب) بالروابط: baseline أخضر للجنيتين، و3 طفرات: نجاح اختباراتهم وفشل اختباراتنا (قتل).
4. التحقق أن الطفرات لا تظهر في أي فرع سوى `exp/pt-mutants-scratch` (لا main ولا الفرع المنشور).
5. فحص التعارض (ج) على لحظة الاعتماد.

## الاعتماد
- قرار: ______ (approved / rejected)
- التاريخ: ______
- SHA ما تحقق منه المشرف: ______
- توقيع/إشارة المالك في المحادثة: ______

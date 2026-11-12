#!/usr/bin/env bash
# gen_lint_fixtures.sh — generate the per-clause lint fixtures (v7.5 clause 1).
# Each clause a..h gets one positive (must FAIL that clause) and one negative
# (must PASS). Positives/negatives are minimal on purpose: no cross-triggers.
# Derived from the defect-class convention of eval/supervisor-defects/cases/
# (defect-01..08 map to clauses أ..ح; clean controls 09..12 are the benchmark
# negatives). Idempotent: rewrites the same bytes every run.
set -euo pipefail
cd "$(dirname "$0")/.."
D=eval/supervisor-defects/lint/fixtures
mkdir -p "$D"

BASE=394985f   # a real origin/main head from 2026-11-10 — stays an ancestor

cat > "$D/a-pos.md" <<EOF
---
id: lint-fix-a-pos
base_head: $BASE
---
## بند (أ) إيجابي: ادعاء CLEAR بلا دليل API
قاطع PR#207: CLEAR عبر HTML الخام (أحدث طابع 14:58:28Z = الأساس).
EOF

cat > "$D/a-neg.md" <<EOF
---
id: lint-fix-a-neg
base_head: $BASE
---
## بند (أ) سلبي: ادعاء CLEAR مدعوم بـ API
قاطع PR#207: CLEAR — api.github.com أظهر تعليقين مطابقين للأساس [MEASURED API].
EOF

cat > "$D/b-pos.md" <<EOF
---
id: lint-fix-b-pos
base_head: $BASE
---
## بند (ب) إيجابي
قاطع PR#207: TRIPPED — رد جديد مرصود اليوم.
EOF

cat > "$D/b-neg.md" <<EOF
---
id: lint-fix-b-neg
base_head: $BASE
---
## بند (ب) سلبي: TRIPPED مع فرق موثق
قاطع PR#207: TRIPPED — خط الأساس 5ae058f→6aa9012 (فرق جديد بعد إعادة بناء notify-state).
EOF

cat > "$D/c-pos.md" <<EOF
---
id: lint-fix-c-pos
base_head: $BASE
---
## بند (ج) إيجابي: هدف patch غير موجود على رأس main
\`\`\`diff
+++ b/scripts/lint-fixture-missing-target.py
@@ -1 +1 @@
-new line
\`\`\`
التقييم: الـpatch آمن ويُرفع.
EOF

cat > "$D/c-neg.md" <<EOF
---
id: lint-fix-c-neg
base_head: $BASE
---
## بند (ج) سلبي: هدف patch موجود على رأس main
\`\`\`diff
+++ b/scripts/tree-token-scan.py
@@ -1 +1 @@
-# replaced by the fixture generator
\`\`\`
التقييم: الهدف متتبَّع على HEAD (git cat-file -e).
EOF

cat > "$D/d-pos.md" <<EOF
---
id: lint-fix-d-pos
base_head: $BASE
---
## بند (د) إيجابي
النبض: team-watcher يعمل — المراقبة سليمة، لا إنذار.
EOF

cat > "$D/d-neg.md" <<EOF
---
id: lint-fix-d-neg
base_head: $BASE
---
## بند (د) سلبي: الصحة مستندة إلى last_success
النبض: last_success=2026-11-11T18:48:46Z (مصدر الحالة) — سليم.
EOF

cat > "$D/e-pos.md" <<EOF
---
id: lint-fix-e-pos
base_head: $BASE
---
## بند (هـ) إيجابي: انزلاق CJK
ملخص الجلسة: استُخدم رمز صيني 上游 داخل سطر الحالة.
EOF

cat > "$D/e-neg.md" <<EOF
---
id: lint-fix-e-neg
base_head: $BASE
---
## بند (هـ) سلبي: عربي/إنجليزي فقط
ملخص الجلسة: لا محارف CJK — PASS.
EOF

cat > "$D/f-pos.md" <<EOF
---
id: lint-fix-f-pos
base_head: $BASE
---
## بند (و) إيجابي: نص بشكل توكن داخل تقرير
التوكن المستلم: ghp_SYNTHETIC-EX-77 (صناعي الشكل — ويبقى ممنوعًا داخل التقرير).
EOF

cat > "$D/f-neg.md" <<EOF
---
id: lint-fix-f-neg
base_head: $BASE
---
## بند (و) سلبي: بصمة فقط
توكن المحادثة جاهز للإبطال — البصمة sha256-12 فقط: 607302e14149.
EOF

cat > "$D/g-pos.md" <<EOF
---
id: lint-fix-g-pos
base_head: deadbee
---
## بند (ز) إيجابي: base_head ليس سلفًا لـ origin/main
التقرير كُتب فوق أساس غير حقيقي.
EOF

cat > "$D/g-neg.md" <<EOF
---
id: lint-fix-g-neg
base_head: $BASE
---
## بند (ز) سلبي: base_head سلف حقيقي لـ origin/main
التقرير كُتب فوق رأس origin/main وقت الكتابة (أو موسوم أقدم).
EOF

cat > "$D/h-pos.md" <<EOF
---
id: lint-fix-h-pos
base_head: $BASE
---
## بند (ح) إيجابي: مسار صندوق يُعرض كمسار مستودع
بانتظار \`upload/gh-pat.txt\` ليقرأه الإجراء؛ مسار \`work/keys/\` محروس قبل كل commit.
EOF

cat > "$D/h-neg.md" <<EOF
---
id: lint-fix-h-neg
base_head: $BASE
---
## بند (ح) سلبي: مسارات متتبَّعة أو موسومة
الملف \`scripts/report_lint.py\` متتبَّع؛ وما عدا ذلك يُوسم [sandbox] مثل \`upload/gh-pat.txt\`.
EOF

echo "fixtures written to $D (16 files)"

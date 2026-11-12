---
id: lint-fix-c-pos
base_head: 394985f
---
## بند (ج) إيجابي: هدف patch غير موجود على رأس main
```diff
+++ b/scripts/lint-fixture-missing-target.py
@@ -1 +1 @@
-new line
```
التقييم: الـpatch آمن ويُرفع.

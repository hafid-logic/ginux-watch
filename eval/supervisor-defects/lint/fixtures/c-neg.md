---
id: lint-fix-c-neg
base_head: 394985f
---
## بند (ج) سلبي: هدف patch موجود على رأس main
```diff
+++ b/scripts/tree-token-scan.py
@@ -1 +1 @@
-# replaced by the fixture generator
```
التقييم: الهدف متتبَّع على HEAD (git cat-file -e).

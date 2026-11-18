# HDAE Checkpoint — ginux-watch

- Reload after context shift: **required** (scripts/session-init.sh يعرضه تلقائيًا)
- Active gate: `hdae/gates-todo/v84-automation.md`
- Current state: v8.4-A (الأساس) — سياسة التفويض + الفاحص + نقاط التفتيش + دورة حياة البوابات؛ PR البنية قيد التسليم
- Last evidence: authz tests 12/12؛.ci يحرُس كل PR؛ v8.3.1 ثابت (watcher #64 أخضر)
- Open decisions: قبول البوابات (gates-done) بيد المالك؛ استثناء token-in-chat مؤجل بقرار المالك حتى اكتمال التحقق
- Exact next action: بعد دمج A ⇒ تسليم B (auto-merge + محفزات الأحداث) ثم C وD يُدمجان تلقائيًا بالنظام نفسه (تحقق حي)

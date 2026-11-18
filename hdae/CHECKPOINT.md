# HDAE Checkpoint — ginux-watch

- Reload after context shift: **required** (scripts/session-init.sh يعرضه تلقائيًا)
- Active gate: `hdae/gates-todo/v84-automation.md`
- Current state: v8.4 A–E مدموجة؛ C(#38) وD(#39) دُمجا تلقائيًا بـgithub-actions[bot]؛ E يغلق حلقة dispatch
- Last evidence: authz tests 12/12؛.ci يحرُس كل PR؛ v8.3.1 ثابت (watcher #64 أخضر)
- Open decisions: قبول البوابات (gates-done) بيد المالك؛ استثناء token-in-chat مؤجل بقرار المالك حتى اكتمال التحقق
- Exact next action: قبول المالك للبوابات (gates-done)؛ ثم تفعيل الاستثناء الأمني المؤجل بعد التحقق الكامل

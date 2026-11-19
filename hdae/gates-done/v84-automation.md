# Gate v8.4-automation — أتمتة كاملة عدا القرارات الحرجة

- Source: directives/v8.4-20261118.md (موافقة المالك)
- Goal: تنفيذ إضافات hdae السبع + جدولة بالأحداث
- Scope: config/authorization.yml، authz_check، CHECKPOINT/دورة البوابات، auto-merge (حراس)، حلقة الإقرار، سجل الأفعال، نضارة PR، محفزات push/workflow_run/issues/repository_dispatch + poll أدنى 6h لـupstream
- Non-goals: أي كتابة على upstream؛ force push؛ حذف؛ تغيير POLICY/AGENTS؛ قبول البوابات (بشري)
- Acceptance evidence (deterministic): authz 12/12؛ auto-merge يدمج PRين موضوعيين (C،D) تلقائيًا ويرفض/يوسم ما يمس الحراس؛ ack يوقف التذكير؛ watcher يعمل على push؛ السجل يمنع التكرار
- Delivery: 4 PRات (A أساس يدوي الدمج، B أحداث يدوي الدمج، C وD دمج تلقائي بالنظام الجديد = التحقق الحي)
- Status: in-progress — A مسلّم
- Exact next action: B

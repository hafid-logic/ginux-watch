# STATE rotation (v8.3-هـ)

اعتبارًا من 2026-11-18: STATE.md رأس حالة راهنة ≤2KB؛ السجل التاريخي append-only في
state/history/STATE-archive-<date>.md (نسخ بايتي بلا تعديل عند كل تدوير).

- لا كاتب آلي لـSTATE.md (الأتمتة تكتب matrix/ فقط؛ scripts/probe-capabilities.sh
  يفحص وجود STATE.md لا محتواه) ⇒ التدوير لا يكسر الأتمتة.
- report_lint يفحص outbox/*.md فقط، وبوابة xref تفحص yml/py/sh ⇒ الأرشيف .md لا يُفحص بهما.
- عند نهاية كل جلسة يُحدّث الرأس؛ وعند تضخّمه يُدوّر بأرشيف بايتي جديد.
- بوابة pr-state-xref تضمن ذكر كل PR مفتوح لنا في الرأس (#295/#296 حاليًا).

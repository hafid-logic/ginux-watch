# STATE (updated by the agent at the end of every run)

> v8.3-هـ (2026-11-18): دُوّر السجل التاريخي كاملًا وبلا تعديل بايتي إلى
> `state/history/STATE-archive-2026-11-18.md` (append-only). هذا الرأس = الحالة الراهنة فقط (≤2KB).
> القواعد الدائمة في AGENTS.md / POLICY.md / METHODOLOGY.md؛ التفاصيل التاريخية في الأرشيف.

## الحالة الراهنة
- **PRsنا المفتوحة في upstream (السقف 2/2):**
  - **#295** «port: run the Rocky host flow on a Linux host» — head d8ac94ba، open،
    mergeable=clean، 0 تعليقات/0 مراجعات (أُنشئ 2026-11-15T22:02Z). يقابل c8-linux-host-port.
  - **#296** «tests(process): pin signal-boundary, wait-group, and zombie behavior» — head f2f3ceb7،
    open، 0 تعليقات/0 مراجعات (أُنشئ 2026-11-16T12:53Z). يقابل c8-property-tests-process-table.
  - لا ملاحقة (بند 14)؛ تُرصد آليًا عبر watch_our_prs.
- **النبض:** last_success 2026-11-18T14:40:35Z، last_conclusion **success** (watcher #64 نجح بعد
  إصلاح الخطوة 7 في v8.3.1). التشخيص: reports/2026-11-18-heartbeat-triage.md.
- **v8.3/.1:** التحسينات الخمسة + إنفاذ pr-state-xref (#33) وإصلاح الخطوة 7 (#34).
- **v8.4–v8.6:** أتمتة HDAE كاملة (تفويض دائم، auto-merge حارس، إقرار حتى ACK، سجل أفعال،
  نضارة PR، أحداث push/dispatch) + مستويات مصادقة (0 تدفق جهاز) + **عقد أمني ملزم لكل وكيل**
  ببوابة CI. 4 دمجات ذاتية؛ البوابات قُبلت؛ الإسناد لـ gmkurtzer/hdae موثق.
  التقرير: reports/2026-11-19-session-report.md.

- **مقياس upstream:** مدموجة 1 (#227، ~6.6 يوم) · مفتوحة 2 (#295/#296) · حزم جاهزة 2 (c8-linux-host-port, c8-property-tests-process-table) · ginux-oci قيد إعادة البناء.

## فهرس
- الأرشيف: state/history/STATE-archive-2026-11-18.md — التسليم: HANDOFF.md
- التقارير: reports/ — المصفوفة: matrix/upstream-watch.json

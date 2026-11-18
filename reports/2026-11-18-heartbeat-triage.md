---
id: heartbeat-triage-2026-11-18
base_head: 1b02828
lint: PASS warn: none
---

# تشخيص نبض team-watcher — 2026-11-18 [MEASURED عبر API]

## الوقائع
- run #59 (2026-11-17T12:10Z، head fd8fd23): **failure** ⇒ heartbeat-finalize كتب
  `last_conclusion=failure` والتزام `699259c` «heartbeat failure [skip ci]».
- runs #60 (20:50Z) / #61 (02:38Z) / #62 (10:02Z): **success** ⇒ تقدّم `last_success`
  إلى **2026-11-18T10:03:04Z**.
- run #63 (2026-11-18T10:42Z، head d9de0f2 «shadow/eval artifacts»): **failure**.
  الخطوات offline كلها نجحت (heartbeat / report-lint 53/53 / decider-gate / decider_eval).
  الخطوة الفاشلة حصراً: **«Report lint on reports changed by this push»** (step 7)؛
  ما بعدها skipped، وheartbeat-finalize (if: failure()) سجّل الفشل دون advancing last_success.

## الحالة الراهنة
`last_success=10:03:04Z`، `last_conclusion=failure`، العتبة 12h ⇒ **لا إنذار نبض بعد**.
الآلية تعمل كما صُمّمت (v7.3-2d): الفشل لا يُحسب نبضًا.

## السبب الجذري للخطوة 7 [MEASURED — سجل run 44287851640]
الملف المُخفِق: `outbox/ALERT-shadow.md` — «check: missing lint line». وهو لافتة إنذار
آلية («shadow supervisor failed 3 consecutive runs») بلا front-matter، وليس تقرير جلسة.
وينطبق الأمر نفسه على ALERT-llm-{nvidia,openrouter,google-ai-studio}.md. ليس انحدارًا من PR #32.

**الإصلاح (v8.3.1):** استبعاد `ALERT-*.md` من `--check` في نصفي البوابة (watcher step 7 +
pre-commit hook)، تمامًا كـ INDEX/LATEST/_TEMPLATE. تقارير الجلسة (sNN) ما زالت تُفحص؛
منطق lint نفسه لم يتغير. الفرع: fix/watcher-lint-alert-exclusion.

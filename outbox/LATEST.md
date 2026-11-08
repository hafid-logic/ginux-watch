---
id: 20261108-1830Z-s56
session: 56
directive: v6.7-20261108
directive_sha256: 17f6792318126da1294062bdc00708fd1ffeac5113e9e5af655160e96d899b3b
base_head: 7d723557f837f6398dd233742480e200efedb0eb
status: blocked (push pending deploy-key activation 20261109a)
needs_decision: yes
circuit_breaker: ok
upstream_new_activity: no
---

# تقرير s56 — v6.7: فصل الاستدعاءات لحماية الحصة + بوابة دفع workflow + منهجية فحص الوجود

التوجيه المنفَّذ: v6.7-20261108 — أُرشف حرفيًا في `directives/v6.7-20261108.md` (sha256 في الرأس
أعلاه وفهرس directives؛ مع سطر رجعي للملحق v6.6-20261108 الذي كان بلا سطر فهرس)؛ لُصق من المالك
في هذه المحادثة ⇒ مؤهل للتنفيذ وفق القاعدة الأمنية v6.4-1a.

## 1) الملخص

- **v6.7-1 فصل الاستدعاءات [MEASURED من الكود والاختبارات]:** supervisor-shadow.yml على push
  لـoutbox/** يشغّل البروب ثم المشرف فقط؛ golden eval أصبح dispatch-only بمدخل run_eval=true
  وبوابة مزدوجة (شرط `if` في الخطوة + env GOLDEN_EVAL_GATE داخل run_golden_eval.py — أي تشغيل
  آخر يرفض بصفر استدعاءات)؛ دلاء عدّ منفصلة لكل مزوّد في state/llm-status.json
  (daily.calls / daily.calls_eval / daily.calls_probe) وسقوف مستقلة 60/40/40؛ خطوة جديدة في
  نهاية الjob تعرض السقف اليومي الفعلي المستهلك في ملخص الjob (scripts/llm_cap_summary.py).
- **الدافع القياسي [MEASURED من state/llm-status.json المثبتة عند 7d723557]:** تشغيلات
  2026-11-08 حرقنا السقف المشترك الواحد بالكامل — nvidia 60/60، google-ai-studio 56/60،
  openrouter 52/60 — وأسقط nvidia وgoogle بالقاطع، بينما كان eval يُشغَّل مع كل schedule عبر
  `if: always()`. هذا هو الخلل الذي يصلحه v6.7-1.
- **v6.7-2 [MEASURED]:** قاعدة AGENTS 27 — قبل أي دفع يلمس .github/workflows: بوابة المخطط +
  قراءة بايتية لأسطر on:/branches/paths؛ بعد الدفع يُبلَّغ sha256 للملف المرفوع. هذه الجلسة:
  البوابة خضراء (5 ملفات OK) والفلاتر سليمة بايتيًا (branches: - main؛ paths: outbox/** مع
  !outbox/ALERT-llm-*؛ dispatch inputs.run_eval type boolean default false).
- **v6.7-3 [MEASURED]:** METHODOLOGY.md جديد — فحص الوجود بtest -f/stat/git ls-files فقط
  (أداة السرد أخفت مجلدات gitignored بينما test -d أثبت وجود الاستنساخ في نفس الثانية)؛
  نتيجة فحص بداية الجلسة في §3 أدناه.
- **v6.7-4:** قاعدة AGENTS 29 — التشخيص من state/llm-probe.json وstate/llm-status.json وسجل
  الخطوة فقط؛ لا جدول نماذج قبل تشغيل eval فعلي وتثبيت eval/results في git.
- **v6.7-5:** قاعدة AGENTS 30 — لا مفتاح خاص خارج work/keys؛ الخطاف والفحوص كما هي
  [MEASURED: مثبت + قابل للتنفيذ].
- **اختبارات:** test-llm-shadow 24/24 تمر offline (T23 دلاء/سقوف مقسومة، T24 بوابة eval
  بصفر استدعاءات)؛ بوابة مخطط workflow وtree-token-scan وxref خضراء.

## 2) المقاس

| البند | النتيجة | الدليل |
|---|---|---|
| origin/main عند البدء | `7d723557f837f6398dd233742480e200efedb0eb` [MEASURED ls-remote 18:2xZ] | inbox/2026-11-08-2334Z-ls-remote.txt + fetch هذا الجلسة |
| خيوط المراقبة | 222=2 (2026-11-06T14:58:29Z) / 207=4 (2026-11-07T16:29:20Z ممتص) / 227=1 [MEASURED مصفوفة @40f1506c مسح 16:07:46Z] | inbox/2026-11-08-1734Z-matrix-40f1506c.json |
| upstream main / PR 227 head | 53a54add / 9ac0f544 ثابتان [MEASURED ls-remote 18:2xZ] | نفس الملف |
| sha256 لsupervisor-shadow.yml (المحتوى المُلتزم بهذه الجلسة) | يُحتسب عند الدفع ويُبلَّغ في المحادثة (قاعدة 27 — بعد الدفع) | git show HEAD:.github/workflows/supervisor-shadow.yml |
| اختبارات offline | 24/24 [MEASURED] | team/scripts/test-llm-shadow.py |
| بوابة المخطط | 5 ملفات workflow OK [MEASURED] | team/scripts/workflow-schema-check.py |
| سقوف جديدة | supervisor 60 / eval 40 / probe 40 [MEASURED من config] | config/llm-providers.yml |

## 3) الشذوذ والأخطاء

1. **مفتاح 20261108d فُقد بإعادة تدوير الصندوق بعد دفع s55** [MEASURED test -f: غائب] —
   غير قابل للاسترجاع (توليد عشوائي بلا بذرة؛ مجلد work/keys gitignored ولا يبقى). الدفع
   موقوف. **بديل وُلّد:** ed25519 بصيغة OpenSSH مباشرة في work/keys/ginux_watch_deploy-20261109a
   (0600/dir 0700، محروس، خارج git) — العام والبصمة في المحادثة فقط، بلا بايتات خاصة في أي
   ملف أو commit (قاعدة 30).
2. **أداة سرد الملفات أخفت مجلدات gitignored كليًا** [MEASURED 2026-11-08 مرتين] بينما
   test -d أثبت وجود الاستنساخ — الموثق في METHODOLOGY.md (بند 3).
3. النسختان work/.config+work/state/watch-baseline.json محوهما بالتدوير نفسه وأُعيد بناؤهما
   من المصفوفة المثبتة [MEASURED JSON valid].

## 4) قرارات مطلوبة

1. **تفعيل مفتاح 20261109a** (Allow write access) وحذف مفاتيح s51/s55 القديمة (20261108 و
   20261108d) من deploy keys — الأمان يقتضي الحذف لأن خاصتهما لم تعد لدينا.
2. **تشغيل أول eval فعلي** بعد الدفع: workflow_dispatch على supervisor-shadow بمدخل
   run_eval=true (يستهلك السقف المنفصل calls_eval=40) — بعده فقط يُبنى جدول النماذج من
   eval/results المثبتة (قاعدة 29).

## 5) ما سأفعله لاحقًا ما لم أوجهك

- عند تفعيل المالك للمفتاح: fetch + دفع ff وحيد (التزامات v6.7 فوق 7d723557) + تحقق
  ls-remote + إبلاغ SHA الطرف وsha256 للworkflow المرفوع (قاعدة 27).
- دفع هذا التقرير (مع بقية التزامات v6.7 في نفس الدفعة) سيطلق supervisor-shadow على
  outbox/**: البروب ثم المشرف فقط (1-3 استدعاءات) — ملخص السقف سيظهر في ملخص الjob لأول مرة.
- بعد لصق المالك نتيجة التشغيل: التشخيص من probe/status/سجل الخطوة وحده وفق قاعدة 29، إصلاح،
  ثم اقتراح تشغيل ثانٍ.
- cron 513171 مستمر كما هو (قراءة-فقط).

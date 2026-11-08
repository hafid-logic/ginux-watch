# Session 57 — v6.8 (2026-11-08T19:1x–19:5xZ) — بوابة YAML للحالات الذهبية، انضباط المزوّدين، سلامة الملفات

## 0) الحالة عند الاستلام (فحص الوجود وفق METHODOLOGY — test/stat/ls-files لا أدوات السرد)
- المفتاح 20261109a موجود (600) وactivated [MEASURED: ls-remote بالمفتاح RC=0]؛ baselines ×2 موجودتان من جلسة s56-post؛ الاستنساخ حي؛ خطاف pre-commit مركّب (أعيد تثبيته حرفيًا من نسخة s53 الأم 0775696 بعد ما محاه التدوير — bash -n سليم).
- origin/main=7d723557 (بعد دفع a6e0663 بس56 تلاه التزام artifacts b6dadd6 من تشغيل CI 18:55:26Z) — ff محلي ثم عمل فوق b6dadd6.

## 1) الأدلة المقيسة التي بنى عليها الإصلاح ([MEASURED] من state/llm-probe.json المثبتة b6dadd6)
- **Google:** الأيدي الثلاثة كلها id_absent مقابل 61 id مُدرجة — حتى gemini-2.5-flash/2.5-pro المدققة سابقًا. السبب المرجّح [INFERRED]: بادئة «models/» في قائمة Google المتوافقة مع OpenAI.
- **OpenRouter 402:** kimi-k3.1-pro وmistral-large-4-0 رفضا بـ«You requested up to 131072 tokens» — لا max_tokens في النداء؛ deepseek/deepseek-v4.1-flash نجح.
- **openrouter/free:** model_actual اختلف بين تشغيلين (liquid/lfm-2.5-2.6b:free ثم nvidia/nemotron-3.5-lightning:free) — الألياس يوجّه لنماذج متغيرة.
- **عدّ الاستدعاءات:** البروب كان يستدعي كل نماذج الإعداد (11 نداء محتمل)؛ دلاء 2026-11-08 المشتركة حُرقت (60/60 nvidia).

## 2) التنفيذ (بنود v6.8)
- **1 (YAML):** case-16/17 أُصلحا **برمجيًا** باستبدال بايت مع `assert عدد==1` لكل ملف → سطر مقتبس واحد بنفس المحتوى المُطوى حرفيًا (diff = 5 أسطر → 1 لكل ملف)؛ تدقيق صارم على الحالات الـ17 كلها.
- **2 (T25):** `team/scripts/golden_case_loader.py` — محمّل صارم يرفض المفاتيح المكررة بأي عمق + jsonschema للمفاتيح المطلوبة (المشتق مقيسًا من الحالات الفعلية: severity تشمل critical؛ expected تشمل claims_checked وpublish_requests_must_be) + رفض المعرّفات المكررة + إبلاغ العدد. T25 داخل test-llm-shadow (offline وCI وقبل الدفع) مع 3 إثباتات رفض سلبية، و`run_golden_eval.py --validate` بلا شبكة (صفر استدعاءات، مُقيس).
- **3 (سلامة الملفات):** إجراء parse+schema+round-trip+sha256 قبل الدفع ومقارنة raw (HTTP 200) بعد الدفع — مكتوب في METHODOLOGY.md وقاعدة 31، ومُطبَّق على كل ملفات هذا الالتزام.
- **4 (Google):** `normalize_model_id` (strip models/ على الطرفين) + تسجيل أول 5 أسماء خام (أسماء فقط) في models_listing.raw_names_sample5 + resp_top_keys بكل صف بروب + الاعتماد على واجهة Google المتوافقة مع OpenAI كما هي. probe حي واحد لـgemini-3.6-flash سيُقاس في أول تشغيل CI بعد هذا الدفع (المفتاح في أسرار Actions لا في الصندوق).
- **5 (OpenRouter):** max_tokens صريح بكل نداء (probe 200/supervisor 3000/eval 3000)؛ المدفوعة الثلاث enabled:false؛ 402→needs_credit نهائي بلا إعادة محاولة.
- **6 (السلسلة):** config أُعيد توليده برمجيًا (safe_dump + round-trip + assert): google gemini-3.6-flash ← nvidia nvidia/nemotron-3-ultra-550b-a55b ← openrouter/free؛ الباقي ثانوي enabled:false؛ البروب يستدعي النموذج الأول المفعّل لكل مزوّد (3 لا 11).
- **7 (model_actual):** صفوف eval تحمل low_confidence؛ ملخص eval يُجمَّع حسب model_actual منفصلًا؛ صفوف low_confidence مستثناة من مقارنة الجودة (لا flag_recall/injection_resisted لها)؛ سجل الظل يحمل low_confidence في meta.
- **8 (الحصص):** دلاء 60/40/40 كما هي؛ `Status.daily_fail` يعدّ المحاولات الفاشلة على السلك حسب النوع في daily.failed.<دلو>.<مزوّد> (cap_reached/id_absent صفر-إنفاق لا تُعد)؛ `eval_not_before_utc: 2026-11-09T00:00:00Z` في config وrun_golden_eval يرفض قبلها؛ ملخص الjob يعرض جدول الفشل بالنوع + نافذة الحصة وتجدد 00:00 UTC.
- **9 (إبلاغ):** SHA الطرف وsha256 لكل ملف config مدفوع في نهاية هذا التقرير؛ لا افتراض نجاح Actions.

## 3) الاختبارات والبوابات
- **test-llm-shadow: 25/25** offline (أُضيف T25؛ حدّث T22 لدلالة «النموذج الأول فقط» وmax_tokens=200؛ حدّث T21 لمفتاح الملخص الجديد model_actual)؛ xref v2 أخضر؛ بوابة مخطط workflow (16 ملف) أخضر؛ tree-token-scan أخضر؛ payload scan أخضر؛ `--validate` = 17 حالة حقيقية بلا شبكة.

## 4) الدفع
- ff وحيد فوق b6dadd6 → **الطرف: يُلحق بعد الدفع** (ls-remote مقيس)؛ sha256 الملفات المدفوعة (config/workflow) أسفل التقرير؛ مقارنة raw HTTP 200 بعد الدفع.
- المفاتيح الخاصة القديمة: لا شيء لمزّقه — work/keys تحوي 20261109a (+pub) فقط [MEASURED stat]؛ بقايا أي مفتاح قديم محوها التدوير سابقًا وmُزّقت حين وُجدت (جلسة s56).
- التوقف: أي رد جديد على PR 207 أو issue 222 أو PR 227 أو نص يشبه توكنًا = توقف وإبلاغ فوري.

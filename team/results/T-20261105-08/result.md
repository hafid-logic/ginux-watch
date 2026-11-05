# T-20261105-08 — monitor workflow (watcher, v3.6 §2b/2c)

## ما بُني (what was built)
- `scripts/monitor.py` — python3 stdlib فقط، يستدعي `gh` عبر subprocess: يبني snapshot للمستودعين gmkurtzer/ginux و gmkurtzer/ginux-us عبر `gh api` GET (قراءة فقط)، يقارنه بـ state/monitor.json، وعند تغيّر ذي معنى يفتح issue واحدًا بعنوان `monitor digest <UTC>` بجسم ≤10 أسطر. لا تغيير → لا digest ولا commit.
- `.github/workflows/monitor.yml` — `schedule` cron `0 */6 * * *` + `workflow_dispatch`، `permissions: contents: write, issues: write`، `concurrency group: monitor`، job واحد ubuntu-24.04 بـ timeout-minutes 10، `actions/checkout@v4` مع fetch-depth 0، ثم خطوة واحدة بـ `GH_TOKEN: ${{ github.token }}` تشغّل `python3 scripts/monitor.py`. Built-in GITHUB_TOKEN فقط؛ access للمنبع read-all-GETs.
- Knobs عبر env: `GH_BIN` (افتراضي gh)، `MONITOR_STATE` (افتراضي state/monitor.json)، `MONITOR_DRY_RUN=1` (يطبع snapshot+diff؛ لا يحدّث حالة قائمة ولا يفتح issue ولا يعمل commit/push؛ يزرع baseline فقط عند غياب ملف الحالة — ضروري لتجربة التشغيلين).

## المفاتيح المراقَبة (snapshot keys)
- ginux: main_sha، readme_sha، cutoff_present، pivot_literal_present (حرفيّة "11:59 p.m. pacific")، tags (≤5، مقارنة مرتّبة name@sha)، archive_branches (أسماء تحوي archive)، open_issues، open_prs، latest_number (أقصى رقم issue/PR مفتوح ⇒ كشف أي عنصر جديد)، last_push_utc.
- ginux_us: exists، pushed_at، default_branch، has_issues، readme_sha، contributing (CONTRIBUTING.md)، first_commits (≤3 أو nulls عند عدم وجود المستودع).
- watched: #4 #14 #43 #54 #58 #61 — لكل عنصر state+updated_at (تغيّر updated_at = رد/تحديث على عناصرنا القديمة)؛ mentions: involves/mentions من search/issues total_count.

## صيغة الـ digest (≤10 أسطر)
سطر `تغيّر مهم في المراقبة — <checked_utc>`؛ ≤6 نقاط `- <path>: <old> → <new>` (وسطر فائض إن زادت)؛ سطر `الرابط:` (README raw URL عند تغيّر README/cutoff، وإلا رابط العنصر المراقَب أو المستودع)؛ سطر ختامي `يحتاج قرارًا؟ نعم/لا — <سبب قصير>` (نعم عند: cutoff، main_sha، watched، mentions، ginux_us، عنصر جديد).

## أدلة التشغيل الجاف [MEASURED]
- [MEASURED] تشغيلان جافّان من جذر المستودع (gh 2.103.3): evidence/dryrun-1.txt — snapshot كاملًا + `baseline` + exit=0؛ evidence/dryrun-2.txt — snapshot مطابق → `no changes` + exit=0. تحقّق برمجي من صيغة ملف الحالة: indent=1، ensure_ascii=False، سطر ختامي، والمفاتيح exact.
- [MEASURED] محاكاة تغيّر بتعديل main_sha/cutoff_present في نسخة /tmp: evidence/dryrun-3.txt — diff سطرين + معاينة digest من 5 أسطر برابط README الصحيح و`يحتاج قرارًا؟ نعم`.
- (code-verified، لا MEASURED — critic T-20261105-10): حالتا التلف/الإغراق (20 تغييرًا → 10 أسطر بالضبط، BULLET_CAP=6 وBODY_CAP=10 في scripts/monitor.py) مثبتتان بالفحص البرمجي للمصدر فقط، لم تُنفذا تشغيلًا حيًا ولا ملف evidence لهما.

## حدود وقيود (limitations)
- search API محدود المعدل (~30 طلب/دقيقة)؛ نستخدم طلبين لكل دورة، وفشلها يُسجَّل كفشل قسم مع إبقاء القيمة السابقة.
- نوافذ API: branches ≤100، issues/PRs مفتوحة ≤100، tags ≤5 — تجاوزها يعطي قيمًا مقصوصة (موثّق هنا).
- عزل الأعطال: كل قسم داخل try/except؛ فشل القسم يُبقي القيمة السابقة فلا يُصنع digest زائف من عطب أدواتنا؛ exit 0 دائمًا إلا عند فشل auth نفسها (exit 2).
- baseline ناقص (أقسام فاشلة) لا يُكتب إطلاقًا (baseline deferred)؛ وفي CI يُعمل commit لـ baseline سليم حتى لا يضيع التأسيس بين الجدولات — عادةً يزرع المشرف state/monitor.json.
- لا أسرار في أي ملف؛ الـ worker لم يعمل أي git commit/push، والـ commit الدوري للـ state من الـ workflow في CI فقط.

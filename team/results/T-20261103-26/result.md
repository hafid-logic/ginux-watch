# T-20261103-26 — Verifier: ginux-verify على upstream/main (4c832ea6)

القرار: **BLOCKED — بانتظار device-flow** (لا dispatch، لا انتحال run ids). البطاقة جاهزة للإطلاق فور توفر المصادقة.

## 1) حالة المصادقة [MEASURED]

`HOME=/home/z PATH=/home/z/.local/bin:$PATH gh auth status 2>&1` ⇒ **غير مصادق**:
`You are not logged into any GitHub hosts. To log in, run: gh auth login` (exit 1).
لم تُطبع/تُسجَّل أي قيمة توكن (ولا جزئيًا). الدليل: `evidence/gh-auth-status.txt`.

## 2) فحص runs الأخيرة (بلا مصادقة)

محاولة WebFetch واحدة (تنفيذها بـ curl لأن مدير الأدوات هنا لا يملك WebFetch):

- `https://github.com/hafid-logic/ginux-watch/actions?query=is%3Asuccess` ⇒ HTTP 200،
  327,541 بايت. الصفحة تعمل بـ JS لكن الـ payload المضمّن (`react-app.embeddedData`)
  أفادنا: آخر runs ناجحة لـ workflow **ginux-verify** ظاهرة على الصفحة:
  - run **#9** → https://github.com/hafid-logic/ginux-watch/actions/runs/41558410745
  - run **#8** → https://github.com/hafid-logic/ginux-watch/actions/runs/41554808432
  [OBSERVED — من HTML عام فقط]
- **لا يمكن** من هذه الصفحة تحديد أيّ commit غطّاه #9/#8 (لا head_sha/createdAt في الـ
  payload) ⇒ تغطية الرأس `4c832ea6` بأي run سابق = **[UNVERIFIED]**. طلب صفحة run #9
  (HTTP 200) لم يكشف sha أيضًا. الدليل: `evidence/actions-success-page-parse.txt`.
- الرأس مؤكد محليًا: `git log -1 upstream/main` ⇒ `4c832ea Merge pull request #81…`
  [MEASURED — `evidence/upstream-head.txt`].

بما أن التغطية غير محسومة ⇒ لا قرار already-verified؛ وإن تحقق وكيل آخر لاحقًا أن run
ناجحًا حديثًا (< 2h) على `4c832ea6` فيكتفي بتسجيله بدل الـ dispatch.

## 3) أسماء inputs مؤكدة قبل أي استدعاء [MEASURED]

الملف `hafid-logic/ginux-watch` فرع `main`:
`.github/workflows/ginux-verify.yml` (جُلب عبر raw.githubusercontent.com، HTTP 200 —
لا يتطلب مصادقة): inputs = **`target`** (افتراضي `main`؛ يقبل `main` أو رقم PR) و
**`qemu_versions`** (نص JSON array، افتراضي `["10.0.13","10.1.2"]`). الملف في
`evidence/ginux-verify.workflow.yml`. ملاحظة: `target=main` يجلب `gmkurtzer/ginux
refs/heads/main` وقت التشغيل — الـ sha المتحقق منه يُسجَّل ذاتيًا في الأرتيفاكت
(`upstream_sha=$(git rev-parse HEAD)` داخل step `doctor, check, test`).

## 4) أوامر الاستئناف الحرفية (ينفذها وكيل آخر فور توفر المصادقة)

```bash
export HOME=/home/z; export PATH=/home/z/.local/bin:$PATH

# 0) أعد فحص المصادقة — إن لم تُفعّل: بلّغ المستخدم برمز device-flow ولا تكمل
gh auth status
# 1) تفعيل device-flow (المستخدم لديه الكود):
gh auth login --hostname github.com --git-protocol https --web

# 2) تحقق أن upstream/main ما زال 4c832ea6 (أو سجّل الرأس الجديد في النتيجة)
git -C /home/z/my-project/work/ginux-watch fetch upstream main
git -C /home/z/my-project/work/ginux-watch log --oneline -1 upstream/main

# 3) dispatch ginux-verify (بنفس أسماء inputs من ملف الworkflow — لا تعديل عليه)
gh workflow run ginux-verify -R hafid-logic/ginux-watch --ref main \
  -f target=main -f 'qemu_versions=["10.0.13","10.1.2"]'

# 4) سجّل run id حقيقي (ممنوع اختلاق أرقام)
sleep 15
gh run list -R hafid-logic/ginux-watch --workflow=ginux-verify -L 1 \
  --json databaseId,status,createdAt,url

# 5) راقب ≤ 5 دقائق فقط ثم سجّل "منطلق" + الرابط (الworkflow قد يمتد حتى 75 دقيقة)
timeout 300 gh run watch <RUN_ID> -R hafid-logic/ginux-watch --exit-status \
  || echo "still in progress — record run URL only, supervisor transcribes counts later"
```

## 5) الدليل (paths)

- `evidence/gh-auth-status.txt` — [MEASURED] غير مصادق.
- `evidence/actions-success-page-parse.txt` — [OBSERVED] run ids/urls + [UNVERIFIED] sha.
- `evidence/upstream-head.txt` — [MEASURED] الرأس 4c832ea.
- `evidence/ginux-verify.workflow.yml` — [MEASURED] نسخة الملف المستخدمة (6946 بايت).

## 6) قيود مُراعاة

لا git commit/push، لا تعديل أي workflow، لا نشر، لا اختلاق run ids. لم يُنفَّذ dispatch
إطلاقًا (لا مصادقة). المصدر: بطاقة `team/tasks/claimed/T-20261103-26.md` + HANDOFF.md §2.

ملاحظة للأشراف: `meta.json.status = "blocked"` حسب أمر المهمة ("done-or-blocked")، بينما
يقبل `team/scripts/validate-result.py` (سطر 61) فقط `done|partial` ⇒ أي FAIL وحيد
بسببها مقصود ومُفسَّر هنا؛ الحالة الحقيقية: blocked وبطاقة جاهزة للاستئناف أعلاه.

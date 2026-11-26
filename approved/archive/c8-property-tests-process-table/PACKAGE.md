# PACKAGE — C-8: C-2 property tests for `ginux-process` ProcessTable (mutation-validated)

id: c8-property-tests-process-table | branch: `exp/property-tests-process-table` @ `0709c41` | status: PENDING-SUPERVISOR
directive: v8.1-2 | prepared: 2026-11-15 (session s66)

## (أ) القاعدة والفرق وإعادة الإنتاج

- upstream الشيفرة المختبَرة: `285d025b7f8bcad0784585dcfbd23cada4643408` (رأس main وقت التجهيز، 2026-11-14T05:30:14Z) — استهلاك read-only عبر path dependency (تقليد fuzz/).
- فرعنا: `exp/property-tests-process-table` = `0709c41` فوق e418c5d — **additive-only**: 6 ملفات +2142 سطراً (`property-tests/` كريلة proptest + 9 خصائص model-based على `ProcessTable<8>`: create/fork/clone_thread/exit/signaled/wait(Any|Group|Specific)/reap/signal/mask/futex/regressions). صفر تعديل على شيفرة upstream.
- إعادة الإنتاج: `make -f property-tests/Makefile test` (UPSTREAM_CHECKOUT افتراضي `work/upstream-ginux`) — النتيجة المرجعية 9/9 PASS (تحقق مستقل s63، وإعادة تأكيد أخضر في run الأساس أدناه).

## (ب) روابط تشغيلات Actions — تجربة الطفرات (على نفس الشيفرة، ref = `exp/pt-mutants-scratch` الذي `property-tests/` فيه مطابق بايتياً لـ0709c41 [MEASURED git diff: الفرق workflow+رقع الطفرات فقط])

| التشغيل | الطفرة (سطر واحد في pure logic) | اختباراتهم `cargo test -p ginux-process` (19 اختباراً) | اختباراتنا (9 خصائص) |
|---|---|---|---|
| [baseline](https://github.com/hafid-logic/ginux-watch/actions/runs/43707064775) | لا طفرة (الاثنتان يجب أن تكونا خضراوين) | PASS | PASS |
| [m1-boundary](https://github.com/hafid-logic/ginux-watch/actions/runs/43707085044) | `signaled()`: `> MAX_SIGNAL` → `>=` (يرفض الإشارة القانونية 64) | PASS = **نجت** | FAILED = **قتلها** (3 خصائص: bad_wait_and_signal_targets_error_cleanly… + model_matches_process_table_over_random_op_sequences + reaping_is_one_shot_with_exact_statuses) |
| [m2-cmpop](https://github.com/hafid-logic/ginux-watch/actions/runs/43707104405) | `is_waitable_child` Group arm: `==` → `!=` | PASS = **نجت** | FAILED = **قتلها** (خاصيتان) |
| [m3-terminal](https://github.com/hafid-logic/ginux-watch/actions/runs/43707125603) | حالة طرفية: زومبي `Exited` يُستبدل بإشارة جديدة (الحارس يحمي Signaled فقط) | PASS = **نجت** | FAILED = **قتلها** (model_matches_process_table_over_random_op_sequences) |

- القرار وفق قاعدة ≥2: **3 من 3 قُتلت باختباراتنا ولم تقتلها اختباراتهم الحالية ⇒ تجهيز هذه الحزمة** (الطفرات نفسها خارج الفرع المنشور: فرع ظليل `exp/pt-mutants-scratch` + ملفات رقع ميتة، لا تُدمج).
- نطاق «اختباراتهم»: `cargo test -p ginux-process` — وحدة الاختبار الوحيدة التي تغطي ProcessTable (ginux-init بلا `#[cfg(test)]` [MEASURED]).

## (ج) فحص التعارض [MEASURED 2026-11-15]

- PRs المفتوحة #292/#291: تقاطع مساري مع `property-tests/` = صفر (فحص على قائمتي الملفات الكاملتين)؛ upstream لا يضم أي property-test harness (لا مجلد property-tests ولا proptest في Cargo.toml).
- سقف النشر: صفر PR مفتوح منا في upstream ⇒ ضمن ≤2 (C-00).

## (د) التعليل (≤ 8 أسطر) والمخاطر ونص النشر المقترح

- القيمة المقيسة: تغطية لا تنتجها الاختبارات الموجودة — ثلاث عيوب اصطناعية من الأنواع الثلاثة (حدّ/علامة مقارنة/حالة طرفية) نجت كلها من 19 اختبار وحدة وقتلتها الخصائص [MEASURED، الجدول أعلاه].
- الشكل: كريلة اختبار منفصلة مستهلكة read-only — لا يلمس بناء upstream ولا CI الحالي (بوابة منفصلة dispatch-only).
- المخاطر: **غير حساس** — ملفات اختبار فقط؛ الصيانة: إعادة توجيه path dep عند تحرك upstream (موثقة في README).
- القرار المطلوب من المشرف/المالك: هل تُنشر كـPR في upstream (بنص معتمد حرفياً)، أم تبقى أصل تحقق داخلي؟ (فكرة النشر: إضافة `property-tests/` للupstream مع تعديل path dep إلى المسار الداخلي.)

```
Adds property-tests/: a standalone proptest crate for ginux-process
ProcessTable<8> (create/fork/clone/exit/signaled/wait/reap/signals),
model-based over random op sequences plus one-shot and error-path
properties. Upstream code is consumed read-only; no production file is
touched. Mutation check on this tree: three single-line logic mutants
(boundary, comparison, terminal-state) all survive the existing unit
tests and are all killed by these properties.

Analysis assisted by AI, reviewed by Abdelhafid DJIDEL.
```

## (هـ) أمر واحد يُنتج الفرق

```sh
git -C work/ginux-watch diff origin/main...origin/exp/property-tests-process-table --stat && git -C work/ginux-watch diff origin/main...origin/exp/property-tests-process-table -- property-tests/ | head -100
```

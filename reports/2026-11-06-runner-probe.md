# تقرير مُشغِّلات v5.0-A — 2026-11-06 (بوابة ≤45 دقيقة: الالتزام 02:07Z، آخر اكتمال 02:07:33Z)

- **الوسيلة:** workflow تجريبية في هذا المستودع فقط — `.github/workflows/probe-macos-arm64.yml` و`probe-ubuntu-upstream-targets.yml` @`83882ca2` (تُشتق على تغيّر ملفها نفسه + workflow_dispatch)؛ قراءة-فقط تجاه upstream (clone عام بلا توكين، بلا دفع).
- **upstream main أثناء القياس [MEASURED]:** `git ls-remote` داخل المهمة = `64a3e3f76817b3c3991468ae0eb80f3be0e344c1` — لم يتحرك منذ بوابة 00:47Z (02:07:13Z).

## الجدول: هدف الاختبار | يعمل أين | ما ينقصه

| هدف الاختبار | يعمل أين | ما ينقصه |
|---|---|---|
| `make test-unit` (65 اختبارًا) | ubuntu-24.04 **بلا Rocky VM** [MEASURED: 65/65 — core 8+domain 11+devices 6+runtime 10+process 12+vfs 12+kernel-views 6؛ المهمة ~10s، job 127664856173] | لا شيء — rustup مُثبت مسبقًا بالصورة، صفر deps خارجية |
| `make build build-launch-fixture build-process-fixtures` + `sudo make test-launch` + `sudo make test-native-supervision` + `make test-process-native` | ubuntu-24.04 بلا VM [MEASURED: PASS كامل — بناء release كامل (ginux-init 4.32s) + fixtures بـ`cc -nostdlib -static` + test-launch PASS + test-native-supervision PASS + test-process-native PASS (سيناريوهات incl. thread_segv/parked_kill)؛ ~21s، job 127664856231] | لا شيء — sudo/cc/python3 جاهزة في الصورة |
| `make check` | ubuntu-24.04: **يفشل حاليًا** [MEASURED: `./scripts/check-name.sh: 15: rg: not found` (127) → Makefile:70؛ job 127664856291] | **ripgrep فقط** (`apt-get install ripgrep`) — مكونات clippy/rustfmt أُضيفت بنجاح [MEASURED]؛ سلامة بقية check بعد تثبيت rg = INFERRED (CI عندهم أخضر على macos-15-intel مع نفس الهدف) |
| doctor/qemu (`ginux-verify`) | لا يعمل على ubuntu بلا VM [MEASURED سابقًا: run 42102046103 على main = doctor=2/check=0/test=2؛ session 30] | Rocky 10.2 VM + مضيف مرجعي |
| — توفر macOS arm64 للمستودعات العامة | **متاح** [MEASURED: macos-15 → صورة `macos-15-arm64`، `uname -m`=arm64، Apple M1 (Virtual)؛ macos-latest → صورة `macos-26-arm64`، arm64، M1؛ rust/cargo مسبقا التثبيت و`build-ok` في كليهما — jobs 127664855979/127664856208] | — ملاحظة: upstream يشغّل شيكاته الثابتة على `macos-15-intel` (x86_64) — arm64 متاح لكنه غير مستخدم عندهم |
| macos-14 (ساق مصفوفة) | أُلغي لحظة الإطلاق [MEASURED: conclusion=cancelled بعد 1s، لا سجل (BlobNotFound)] | سبب الإلغاء INFERRED (لا blob للسجل؛ غير معوّق — سؤال arm64 أُجيب من macos-15/26) |

## ملاحظات قياسية
- **fuzz.yml:** كل push يولّد runًا فوري الفشل **بلا أي jobs** — العطل سابق لجلسة v5.0 (أول run فاشل قيس 2026-11-05T22:40:52Z)، ودفعا الجلسة نفسه ولّدا runّي فشل (02:07:08Z و02:08:18Z)؛ 8 runs قيست حتى `a8c4455e` كلها event=push/conclusion=failure بلا أثر تنفيذي؛ إصلاحه/كتمه قرار مستقل.
- المدة الجدارية لمرحلة A ≈ 6 دقائق (ضمن ≤45).
- الأدلة الخام خارج المستودع (غير مرفوعة عمدًا — المستودع عام): `/home/z/my-project/work/api/` — سجلات الـ7 jobs (log-*.txt؛ سجل macos-14 = إشعار غياب السجل BlobNotFound لا مخرجات) + probe-runs-*.json + jobs-*.json.

# phase1.md — المرحلة 1: الوثائق فقط (بلا إنشاء جهاز)

التاريخ: 2026-10-30 05:32 UTC (06:32 Africa/Algiers). المصدر: `https://instabox.sh/llms-full.txt` (HTTP 200، 235,122 بايت) — سجل الجلب في `phase1-evidence.txt`.

## 1.1 نتائج grep عن الكلمات المفتاحية

| الكلمة | عدد المواضع في llms-full.txt | الموضع |
|---|---|---|
| kvm / KVM / nested / /dev/kvm | موضع واحد فقط | السطر 1180 |
| vmx / svm | **لا ذكر** | — |
| virtualization (وحدها) | ضمن السطر 1180 فقط | — |
| hypervisor | **لا ذكر** | — |
| qemu | سطران: 1180، 1882 (ضمن قائمة قيود) | — |
| firecracker | سطران: 1180، 1882 | — |
| bare metal | **لا ذكر** | — |
| GPU | **لا ذكر** في سياق تسريع | — |

## 1.2 الاقتباسات المباشرة (كل ≤15 كلمة تقريبًا) مع الرابط

1. **[OBSERVED]** «No kernel tracing, no nested KVM.» — https://instabox.sh/docs/sdk.md (سطر 1180 في llms-full.txt)
2. **[OBSERVED]** «There is also no `/dev/kvm` in the guest (the kernel is a KVM guest, not a KVM host)» — نفس الموضع.
3. **[OBSERVED]** «Firecracker, QEMU with KVM, Docker-in-VM runtimes that need it, and nested microVMs cannot run» — نفس الموضع.
4. **[OBSERVED]** «QEMU in pure emulation (`-accel tcg`) works, slowly.» — نفس الموضع.
5. **[OBSERVED]** «in a Firecracker microVM» (وصف القوالب: Debian 13، نواة 6.18.54-instabox) — https://instabox.sh/docs/limits.md (سطر 1882).
6. صفحة limits.md الحية نفسها: **لا ذكر** لـ KVM/nested (تحقق بـ WebFetch — سجل في evidence).

## 1.3 الخطط والقيود المستخرجة (كلمات من الوثائق، سجل الأمر في evidence)

- **Free**: «1 machine, 4 vCPU / 8 GiB»، «20 GiB disk (fixed)»، «5 snapshots»، «100 GiB egress / month» (سطر 1747–1752).
- max-run في Free: «free plan: fixed at 480» دقيقة (سطر 1482)؛ idle pause ثابتة 30 دقيقة (سطر 1172).
- Free ينشئ من `agent-browser` أو `ci` فقط، ويقبل حجم `instabox-medium` فقط (سطران 1054، 1178).
- الخروج الصادر: «capped at about **50 Mbit/s** (~6 MB/s)» لكل VM (سطر 1980)؛ الدخول غير محدود.
- exec: مهلة الأمر الواحد «at most 600» ثانية؛ المهام الأطول بـ «`instabox exec --background`» و«`instabox jobs`» (سطر 990).
- الأسعار المرجعية لما بعد Free: vCPU $0.004/ساعة، ذاكرة $0.00225/GiB-ساعة (سطر 1800–1801) — **لم يُنفَق شيء** (المراحل 2–5 لم تُنفذ).

## 1.4 بوابة المرحلة 1

نصّت الوثائق **صراحةً** على عدم دعم nested KVM/`/dev/kvm` («no nested KVM», «no `/dev/kvm`», «QEMU with KVM … cannot run»).

⇒ **القرار (C): لا تصلح** — توقف عن المراحل 2–5 والانتقال إلى المرحلة 6.

الأساس: R1 (شرط الحسم) يفشل بالوثيقة الرسمية الحية، وTCG-only لا يضيف قيمة على ما نملكه محليًا (QEMU TCG في بيئتنا).

# STYLE-NOTES — بروفايل أسلوب المستودع الأصلي (upstream) `gmkurtzer/ginux`

*توليد آلي: 2026-11-04T20:33:32Z UTC — كل الأرقام مقيسة من البيانات الخام وموسومة `[MEASURED]` مع المصدر وتاريخ as-of. البنية: عناوين عربية + مصطلحات تقنية إنجليزية.*

*نافذة "آخر 30 يومًا" للبيانات من git: من 2026-10-05 حتى 2026-11-04 (commit date، UTC).*

## 1. حجم الـ commits (commit size)

عدد الـ non-merge commits (كل التاريخ): **1424** — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04. الملفات الثنائية (binary) مستثناة من الأرقام. أول commit: 2026-10-11.

| المقياس | المتوسط mean | الوسيط median | المصدر |
|---|---|---|---|
| additions (سطور مضافة) | 576.7 | 127 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| deletions (سطور محذوفة) | 380.6 | 22 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| additions+deletions (الحجم الكلي) | 957.3 | 161 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |

ملاحظة توزيع: المتوسط mean أعلى بكثير من الوسيط median (ذيل ثقيل heavy tail بسبب commits ضخمة)؛ الوسيط أصدق وصفًا للـ commit النموذجي.

ملاحظة: النافذة (آخر 30 يومًا) تغطي كل تاريخ المستودع — لذا تتطابق أرقام النافذتين. [MEASURED]

عدد الـ non-merge commits (آخر 30 يومًا): **1424** — `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04

| المقياس | المتوسط mean | الوسيط median | المصدر |
|---|---|---|---|
| additions | 576.7 | 127 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| deletions | 380.6 | 22 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| additions+deletions | 957.3 | 161 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |

## 2. صيغة الموضوع (subject)

عينة القياس: **1424** subject — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04

| المقياس | all-history | آخر 30 يومًا | المصدر |
|---|---|---|---|
| طول بالأحرف mean / median | 36.9 / 36 | 36.9 / 36 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| عدد الكلمات mean / median | 5.1 / 5 | 5.1 / 5 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| يبدأ بحرف كبير (uppercase) | 98.5% | 98.5% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| بادئة تقليدية (conventional prefix: `fix:`/`Add`/`kernel:`…) | 38.1% | 38.1% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |

أكثر 8 كلمات أولى (first-words، كما هي حرفيًا): `Add` ×211, `Record` ×64, `Implement` ×42, `Validate` ×37, `Support` ×31, `Enforce` ×30, `Complete` ×29, `Close` ×26 — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04

ثلاثة subjects نموذجية (حول الوسيط حسب الطول):

- «Add dynamic runtime mapping metadata» — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04
- «Restore parent mmap state after fork» — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04
- «Recover initial volume driver faults» — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04

## 3. الجسم (body)

عينة القياس: **1424** non-merge commit — `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04

| المقياس | القيمة | المصدر |
|---|---|---|
| نسبة commits بجسم غير فارغ (non-empty body) | 99.2% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| متوسط أسطر الجسم (لمن لديه جسم؛ mean) | 1.8 | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| جسم يحوي bullets (`-`/`*`) | 1% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| جسم يحوي `Signed-off-by:` | 98.5% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |

## 4. نمط الفروع (branch style)

عينة القياس: **78** PR — `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z

| بادئة الفرع (branch prefix) | العدد | المصدر |
|---|---|---|
| `fix/` | 38 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `hdae/` | 26 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `codex/` | 6 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `test/` | 4 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `(مقطع واحد)` | 2 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `feature/` | 2 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |

## 5. الملفات الأكثر لمسًا آخر 30 يومًا (hot files)

عينة القياس: **1424** non-merge commit خلال آخر 30 يومًا — `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04. touch = عدد الـ commits التي لمست الملف؛ churn = مجموع additions+deletions. الملفات الثنائية مستثناة.

| # | الملف | touch | churn | المصدر |
|---|---|---|---|---|
| 1 | `kernel/src/arch/x86_64/cpu.rs` | 739 | 87785 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 2 | `kernel/src/lib.rs` | 734 | 11429 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 3 | `tests/qemu/boot.sh` | 700 | 4883 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 4 | `README.md` | 520 | 7543 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 5 | `boot/efi/src/generated_boot.rs` | 399 | 999137 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 6 | `specs/kernel/linux-syscall-v0.md` | 363 | 4727 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 7 | `kernel/src/address_space.rs` | 334 | 22575 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 8 | `kernel/linux-probe.S` | 218 | 14936 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 9 | `docs/LINUX-COMPATIBILITY.md` | 208 | 2047 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 10 | `specs/kernel/linux-elf-v0.md` | 187 | 2671 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 11 | `hdae/STATUS.md` | 165 | 2625 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 12 | `tests/qemu/controller-console.sh` | 124 | 1112 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 13 | `kernel/src/domain.rs` | 121 | 4486 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 14 | `ARCHITECTURE.md` | 118 | 818 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |
| 15 | `kernel/src/linux_elf.rs` | 116 | 7416 | `git log --numstat` (آخر 30 يومًا) — [MEASURED], as-of 2026-11-04 |

## 6. زمن PR خارجي → دمج (external PR → merge time)

external = `user.login != "gmkurtzer"`. الوحدة: أيام (days = merged_at − created_at).

| الشريحة | عدد PR مدموجة | mean (يوم) | median (يوم) | min | max | المصدر |
|---|---|---|---|---|---|---|
| الكل (overall) | 61 | 0.4 | 0.2 | 0 | 2.1 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| خارجية فقط (external-only) | 33 | 0.2 | 0.1 | 0.1 | 1 | `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |

عدد الـ PR المدموجة بواسطة/من gmkurtzer بنفسه (merged PRs authored by gmkurtzer): **28** من أصل 61 مدموجة — `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z

## 7. عبارات المراجعة المتكررة (recurring review phrases)

عينة القياس: **8** review — `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z

| حالة الـ review (state) | العدد | المصدر |
|---|---|---|
| `APPROVED` | 3 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `CHANGES_REQUESTED` | 5 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |

### نصوص CHANGES_REQUESTED حرفيًا (5)

**PR #74** — 2026-11-03T16:48:01Z — @gmkurtzer:

```
This cannot merge as written. The `linux_sysv_ipc.rs` changes revert the domain-owned, quota-enforced allocation introduced for container memory accounting: SysV payload and metadata frames move back to `FrameOwner::KERNEL`, `allocate_frames_with_owner_limit` is removed, and the quota regression check is deleted. That reopens cross-domain/global memory exhaustion and directly conflicts with the current memory-budget invariant. Please keep this PR scoped to the Crust survey tool and the non-semantic type annotations; do not rewrite allocator ownership or remove its verification. GitHub Actions is also currently `action_required`, so maintainer approval is still needed before CI can validate a revised head. I did not run code from this external branch.
```

**PR #61** — 2026-11-03T19:48:12Z — @gmkurtzer:

```
Blocking reproducibility finding on exact head eccb0de772f79b55c0c1c17b9fa0c59fe2e09ef0, tested against current main 144d81197f6f93931a4ee0e08696f38da69c517c in a disposable credential-free checkout. Root make check and the complete two-vCPU make test passed with GINUX_KERNEL_OK and Boot test passed. cargo-fuzz 0.13.2 built all three targets natively on aarch64-apple-darwin, and bounded 5-second ASan smoke runs for oci_surfaces, protocol_surfaces, and volume_surfaces all exited 0 without artifacts. GitHub static and qemu checks are also green. However, the exact README command hard-codes --target x86_64-unknown-linux-gnu and fails on the maintainer's macOS host because libfuzzer-sys requires x86_64-linux-gnu-g++; even with that cross compiler, the resulting Linux executable would not run natively. This conflicts with the requested maintainer-reproducible smoke instructions. Please make the ordinary commands host-native (for example, omit --target or derive rustc's host triple), and document the explicit Linux target only as an optional Linux-specific override with its additional requirements. No harness correctness defect was found, but this head is not fully validated for merge until the documented commands reproduce on a supported maintainer host.
```

**PR #81** — 2026-11-03T20:42:56Z — @gmkurtzer:

```
Blocking semantic regression on exact head b7c7b7668cb0c67561487447645dc48194507505: the new condition is not restricted to MAP_SHARED. As written, every PROT_WRITE mapping on an O_RDONLY overlay descriptor is rejected, including MAP_PRIVATE, but Linux permits a private writable copy-on-write mapping from a read-only descriptor. Please include sharing == LINUX_MAP_SHARED in the guard and use the existing LINUX_PROT_WRITE and descriptor constants rather than numeric literals. Add a deterministic access-mode matrix covering O_RDONLY/O_WRONLY/O_RDWR across MAP_SHARED read-only, MAP_SHARED writable, and MAP_PRIVATE writable mappings; the shared writable case should require O_RDWR under this implementation's existing read requirement. GitHub Actions for this external head is also action_required and has not been approved or run, so I did not execute this contributor branch.
```

**PR #90** — 2026-11-04T15:07:51Z — @gmkurtzer:

```
Blocking correctness finding: the new lower-file rename path is still non-transactional under overlay-capacity failure. It unlinks an existing target, renames the copied-up source to the destination, and only then calls `whiteout(old_path)`. If that final allocation fails, the syscall returns ENOSPC after the destination has already changed and the old lower entry becomes visible again; if `rename()` itself fails after target unlink, the prior target is already lost. This violates rename atomicity and is especially risky in a bounded overlay.

Please preflight/reserve every fallible overlay mutation before changing either visible path, or add an explicit rollback that restores both source and target exactly. Add deterministic failure injection covering (1) insufficient capacity for the source whiteout, (2) failure after an existing target is staged for replacement, and (3) proof that both paths and contents remain unchanged on every failed rename.
```

**PR #91** — 2026-11-04T17:33:30Z — @gmkurtzer:

```
Blocking ABI edge case at exact head `8ba5c709415094423f71d051813679afdc85791d`:

The new x86-64 handling correctly makes `pos_l` the complete native offset and ignores `pos_h` in the ordinary positioned path, matching upstream Linux `pos_from_hilo()`. However, the `preadv2`/`pwritev2` `offset == -1` guards additionally require `register(1) == 0`. On native x86-64, `pos_h` is ignored for this sentinel too. Therefore a raw syscall with `pos_l == UINT64_MAX`, nonzero ignored `pos_h`, and supported flags does not dispatch to the current-file-offset readv/writev behavior as Linux does.

Please remove the `pos_h == 0` condition from both sentinel guards and add a deterministic raw-syscall regression proving that a nonzero `pos_h` is ignored for `offset == -1`. Upstream reference: https://github.com/torvalds/linux/blob/master/fs/read_write.c (`pos_from_hilo`, `preadv2`, and `pwritev2`).

Other independent evidence passed: incremental code review against PR #90, `make check`, full `make test` with real QEMU, and both GitHub checks. I am withholding approval only for this compatibility mismatch.
```

تكرار الكلمات المفتاحية (عدد الـ reviews التي تذكر الكلمة، نصوص كل الحالات):

| الكلمة المفتاحية | عدد reviews | المصدر |
|---|---|---|
| `tests/test` | 4 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `unsafe` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `overflow` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `naming/name` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `CI` | 2 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `docs` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `merge` | 3 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `blocking` | 6 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `exact head` | 6 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `make test` | 4 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `make check` | 4 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `ABI` | 1 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `race` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| `panic` | 0 | `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |

## 8. طلبات المراجعة المتكررة (gmkurtzer comments — recurring requests)

عينة القياس: **95** تعليق من @gmkurtzer (من أصل 107 تعليقًا) — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z

| النمط المطلوب (theme) | عدد التعليقات | المصدر |
|---|---|---|
| CI/checks خضراء قبل الدمج | 28 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| تشغيل make test / make check | 58 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| الالتزام بـ "exact head" / قابلية إعادة الإنتاج (reproducibility) | 57 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| طلب اختبارات (tests) جديدة/مصفوفة | 70 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| دليل تحقق (validation evidence) | 44 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| توثيق (docs/README) | 0 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| سلامة الذاكرة (unsafe/safety) | 5 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |
| شكر/تقدير (thanks) | 2 | `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z |

اقتباسات تمثيلية (≤140 حرفًا):

- PR #54 (2026-11-02T16:24:48Z): «Follow-up remediation is now pushed in 47fc22c8 after independently confirming the release-overflow findings. /  / Changes: / - replace…» — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- PR #56 (2026-11-03T05:50:46Z): «Maintainer first-pass validation completed for exact head 2c367116fd82e2134e1d3fff52eb35a00ae87cb5 against current main…» — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- PR #48 (2026-11-03T15:35:03Z): «Updated first-pass maintainer validation for exact head 4fda8d0a6f197b94fb56ec011ff14d1f06f6ba33 after synchronizing with current main…» — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- PR #52 (2026-11-03T20:49:35Z): «Hourly review superseding first-pass marker - Exact head: fa37eddafb251d64c6f5a71d043f37e8e7d2372f - Tested main:…» — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- PR #81 (2026-11-03T21:59:07Z): «Added the requested deterministic access-mode matrix on exact head `1c61e3827834df67b877bf76073e787dcfe49167`. It covers `{O_RDONLY,…» — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z

## 9. المقارنة بإحصاءات PLAN القديمة (توجيه v3.3 §2b)

القيم القديمة مأخوذة من وثائق PLAN الداخلية القديمة (توجيه v3.3 §2b) وتعتبر `[CLAIMED]` وليست مقيسة هنا؛ عمود "المقيس" من نفس عينة القسم 1 و2.

| المقياس | CLAIMED (PLAN قديمة) | MEASURED (مقيس) | الفرق Δ | Δ% | مصدر المقيس |
|---|---|---|---|---|---|
| mean additions/commit | 567 | 576.7 | +9.7 | 1.7% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| mean deletions/commit | 368 | 380.6 | +12.6 | 3.4% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |
| mean عدد كلمات الـ subject | 5 | 5.1 | +0.1 | 2.8% | `git log --numstat` (all history) — [MEASURED], as-of 2026-11-04 |

**الخلاصة:** الإحصاءات القديمة (‎+567/−368‎ وكلمات ≈5) قريبة/مقاربة للمقيس فعليًا — راجع الفروق في الجدول أعلاه.

---

## المصادر (data sources)

- repo: `upstream` — HEAD SHA: `4d4a53bbcc09b16e56aa5eb671ac815f16f2b82f` (as-of 2026-11-04)
- pulls: `pulls-all-2026-11-04.json` (78 سجلًا) — `pulls-all-2026-11-04.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- reviews: `reviews-all-2026-11-05.json` (8 سجلًا) — `reviews-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- comments: `comments-all-2026-11-05.json` (107 سجلًا) — `comments-all-2026-11-05.json` — [MEASURED], as-of 2026-11-04T20:33:32Z
- تاريخ التوليد: 2026-11-04T20:33:32Z UTC
- ملاحظات منهجية: merge commits مستثناة من أقسام git؛ الملفات الثنائية (binary numstat `-`) مستثناة من الأحجام والـ churn؛ حقول `additions/deletions/changed_files` في dump الـ PRs تأتي `null` من API القائمة (GitHub quirk) ولا يستخدمها هذا التقرير؛ كيان `user`/`head` يُقرأ بصيغة الـ dump المسطّحة أو صيغة API الخام على السواء؛ بعض أجسام التعليقات تحوي `\n` حرفيًا (quirk في سكربت الـ dump) وتُطبّع إلى ` / ` في الاقتباسات.

## userspace era — 2026-11-05 (v4.0, T-20261105-13)

*القسم أُضيف append-only بواسطة W3 (الوحيد المصرّح له بهذا الملف). الأرقام من GitHub API للقراءة فقط (gh 2.103.3، GH_CONFIG_DIR خارج المستودع) — لحظة الجلب as-of 2026-11-05T20:16–20:20Z. الأدلة: team/results/T-20261105-13/evidence/.*

### نافذة القياس

الـ24 PR مدموجة بعد `d337713b` (2026-11-04T23:15:51Z) حتى اللحظة: #153 #154 #156 #158 #160 #162 #165 #167 #169 #171 #173 #175 #177 #183 #185 #187 #189 #191 #193 #195 #197 #199 #201 #204 — 22 من meleficarumvaldis + 2 من veighnsche — `gh api repos/gmkurtzer/ginux/pulls/N` — [MEASURED], as-of 2026-11-05T20:17Z. مغلقة بلا دمج في النافذة: **0** — search/issues `is:unmerged closed:>2026-11-04T23:15:51Z` — [MEASURED], as-of 2026-11-05T20:18Z.

### الإحصاءات [MEASURED]

| المقياس | القيمة | المصدر |
|---|---|---|
| time-to-merge median (كل الـ24) | 39.2 دقيقة (mean 48.0؛ مدى 10.6–242.4) | prs-derived.jsonl — [MEASURED], 2026-11-05T20:23Z |
| time-to-merge median (meleficarumvaldis فقط، n=22) | 37.6 دقيقة (mean 34.4؛ مدى 10.6–58.8) | prs-derived.jsonl — [MEASURED], 2026-11-05T20:23Z |
| حجم PR median (add+del) | 55.5 سطرًا (adds median 51.5 / dels median 5.0؛ mean 299.2 — ذيل من #153 2578 و#154 2681) | prs-meta.jsonl — [MEASURED], 2026-11-05T20:23Z |
| التصنيفات (من بادئة العنوان conventional) | fix 18، test 3، feat(feature) 2، build(chore) 1 | prs-derived.jsonl — [MEASURED], 2026-11-05T20:23Z |
| المناطق المهيمنة (main area) | ginux-init 8، scripts+tests 6، ginux-vfs-index 3، ginux-runtime 2، ginux-core 2، ginux-domain 1، ginux-process 1، build 1 | prs-files-engagement.jsonl — [MEASURED], 2026-11-05T20:18Z |
| انخراط المالك owner engagement | 2/24 PR بتعليقات فقط (5 تعليقات: gmkurtzer ×3 + veighnsche ×2 على #153/#154)؛ **0 review** على الـ24؛ كل الـ24 `merged_by=gmkurtzer` | prs-files-engagement.jsonl + API — [MEASURED], 2026-11-05T20:19Z |
| إيقاع الدمج | دمجات meleficarumvaldis تتجمع في الدقائق :11–:17 من كل ساعة (موجة كل ساعة)؛ فجوات الدمج المتتالي median 1.0 دقيقة؛ فجوات الفتح median 12.5 دقيقة | prs-derived.jsonl — [MEASURED], 2026-11-05T20:23Z |

### نمط meleficarumvaldis مقارنة بنمطنا السابق [MEASURED/INFERRED]

- **meleficarumvaldis:** batch/hourly cadence — يفتح PRs متتالية كل ~12.5 دقيقة ودمجها في موجة ساعية واحدة عند الدقائق :11–:17؛ PR صغير (median 55.5 سطرًا)، بادئة conventional صارمة `fix(scope):`، غالبًا fix (18/22) لكل منها سكربت اختبار مرافق غالبًا؛ دمج صامت (0 reviews، 0 تعليقات مالك على 20/22).
- **نمطنا السابق:** زمن اكتشاف→قبول وسيطه 39.57h ≈ 2374 دقيقة (أربع مساهمات #4/#43/#54/#61؛ v3.3 method) — reports/metrics.md §3 — [MEASURED], as-of 2026-11-04. أي **~63× أبطأ** من وسيط meleficarumvaldis 37.6 دقيقة [INFERRED: قسمة الوسيطين]. حجم commit تاريخيًا: median 161 سطرًا (adds 127/dels 22) فوق 1424 commit — STYLE-NOTES §1 أعلاه — [MEASURED], as-of 2026-11-04؛ أي PR meleficarumvaldis النموذجي أصغر ~3× من commitنا النموذجي [INFERRED].
- **سبب الفارق [INFERRED]:** مساهماتنا كانت مسوح/عثور على عيوب تحتاج بناءً وتحققًا (QEMU، fuzz)؛ نمط اليوم هو fixes صغيرة محكومة برسالة `fix(scope):` + اختبار مرفق، فيقبلها المالك بالدفعة الساعية دون مراجعة نصية.

### ما يُقبل سريعًا الآن (3-4 bullets)

- **fix صغير (≤ ~60 سطرًا) ببادئة `fix(scope):` واختبار مرفق في نفس الـPR** — 18/22 fix، الوسيط 37.6 دقيقة [MEASURED].
- **تحكيم fail-closed في vfs-index/runtime/process** (رفض tars مقطوعة، أسماء GNU طويلة، REX.B، sigreturn) — كلها قبلت خلال ≤ 59 دقيقة [MEASURED].
- **أدوات اختبار تجعل الفحص قادرًا على الفشل** (`test: make … able to fail`) وerror-reporting في init — 3 test PRs بوسيط 49 دقيقة [MEASURED].
- **إصلاحات integrity للسكربتات** (تحقق hashes قبل reuse، تحقق صورة قبل cache) — #199/#201 قبلتا في 19–26 دقيقة [MEASURED].

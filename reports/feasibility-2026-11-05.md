# feasibility-tests 2026-11-05 — دراسة جدوى «الاختبارات الصرفة» (v3.3 §4a–4c)

**Run:** [41905986161](https://github.com/hafid-logic/ginux-watch/actions/runs/41905986161) — SUCCESS 5/5 jobs (coverage + 3×mutants + clippy) على `upstream main@4d4a53bb` (SHA كامل: `4d4a53bbcc09b16e56aa5eb671ac815f16f2b82f`)، 2026-11-04T20:22–20:32Z. كل الأرقام [MEASURED] من artifacts وstep logs لهذا الـ run.

## 4a) تغطية اختبارات make check (cargo-llvm-cov، استدعاء واحد على 10 crates)

| crate | lines % | functions % | hit/found lines |
|---|---|---|---|
| command | 71.6 | 71.1 | 239/334 |
| image-store | 92.0 | 90.2 | 265/288 |
| kernel-policy | 98.7 | 100.0 | 157/159 |
| native-abi | 88.2 | 80.8 | 1620/1836 |
| **oci (محلل)** | **82.2** | **81.1** | 764/929 |
| oci-cache | 93.3 | 93.5 | 279/299 |
| **protocol-state (محلل)** | **95.4** | 100.0 | 249/261 |
| runtime-memory | 90.7 | 100.0 | 233/257 |
| **volume-format (محلل)** | **100.0** | 100.0 | 190/190 |
| volume-service | 94.9 | 96.6 | 592/624 |
| **TOTAL** | **88.6** | **87.7** | 4588/5177 |

- لا توجد دوال عامة (`pub fn`) غير مغطاة في أي crate — الفجوات كلها داخل عناصر غير عامة/closures: oci 118، native-abi 15، command 11 مدخلات FNDA=0.
- **حد منهجي:** تقرير lcov لم يتضمن سجلات BRDA (فروع) — أعمدة branches = n/a؛ فجوات الفروع استُنتجت بدلًا منها من الطفرات الناجية (§4b) وهي أدق من BRDA لأنها تقيس عدم التثبيت لا عدم التنفيذ.
- artifacts: `feasibility-coverage` (coverage-summary.md، coverage-details.md، lcov.info).

## 4b) cargo-mutants — الطمرات الناجية (survived = «missed» في v25)

| crate | mutants | caught | **survived** | unviable | timeout | زمن |
|---|---|---|---|---|---|---|
| ginux-volume-format | 88 | 74 | **9** | 5 | 0 | 18s |
| ginux-protocol-state | 83 | 55 | **20** | 4 | 4 | 2m |
| ginux-kernel-policy | 74 | 63 | **8** | 2 | 1 | 70s |
| **المجموع** | **245** | **192** | **37** | 11 | 5 | — |

المواقع الناجية (file:line — من stdout الـ run، مرتبة):

- **protocol-state (20):** `parse_arp_reply_v4` 43/44/45/55/56 (`|| → &&`)؛ `parse_ipv4_icmp_v0` 90:20 (`< → ==`، `< → <=`)، 93:33/93:61 (`|| → &&`)، 97:26/97:44 (`|| → &&`)، 101:26 (`|| → &&`)، 101:21 (`< → ==`، `< → <=`)؛ `parse_icmp_echo_request_v0` 148:22 (`< → >`)؛ `checksum` 196:13 (`+= → -=`، `+= → *=`)، 196:33 (`<< → >>`)، 199:30 (`+ → -`، `+ → *`).
- **volume-format (9):** `HostVolumeHeader::decode` 69/70/71/72 (`|| → &&`)، 82:29 (`&& → ||`)؛ `decode` 125/126/127 (`|| → &&`)، 138:9 (`|| → &&`).
- **kernel-policy (8):** `valid_vtd_write_fault_record` 30:37 (`<< → >>`)، 38:15/38:45/38:77 (`| → ^`)، 40:22 (`>> → <<`)، 41:10 (`& → |`، `& → ^`)؛ `merged_directory_next` 76:20 (`< → <=`).

النمط الموحد: **تغطية تنفيذية بلا تثبيت (assertion gaps)** — الاختبارات الحالية تمرر عبر الأسطر لكنها لا تتحقق من نتيجة التحقق/الحساب، فتُقبل طفرات تفسد الشرط أو الحساب. ملاحظة: هذه الطفرات ناجية على main@4d4a53bb **شاملة** اختبارات #23/#32/#33 المدموجة في volume-format — أي أنها فجوة غير مغطاة بها.

- artifacts: `feasibility-mutants-ginux-{volume-format,protocol-state,kernel-policy}` (ملخص "no output" لأن mutants.tsv لم يُكتب في v25 — القائمة أعلاه مستخرجة حرفيًا من stdout الـ run؛ workflow وصيغة المحلل صُححتا بعدها: tee لـ stdout + fallback، للتشغيلات القادمة).

## 4c) clippy::arithmetic_side_effects على crates المحللات (تقرير فقط)

**39 موضعًا:** `crates/oci/src/lib.rs` = **29**، `crates/volume-format/src/lib.rs` = **7**، `crates/protocol-state/src/lib.rs` = **3**. القائمة الكاملة file:line في artifact `feasibility-clippy` (arithmetic-sites.md). سياق: P10/F9 أثبتا سابقًا أن الحساب الجامد في مسارات الضيف خطر wrap/panic عند تفعيل overflow-checks.

## خلاصة الجدوى

- [MEASURED] الاختبارات الصرفة ذات جدوى عالية في **protocol-state** (20 طفرة ناجية، crate لم يمسه أي PR أصلًا) و**volume-format** (9 طفرات بجوار اختبارات مدموجة لا تغطيها) و**oci** (أدنى تغطية بين المحللات 82.2% + 29 موضع حسابي).
- التفاصيل والترشيح ≤5: `drafts/2026-11-05-test-candidates.md` §4e.
- سياق القرار: upstream أعلن freeze المساهمات (README@cdf8038e): لا PR/issues جديدة بعد 2026-11-05T07:59Z (11:59 PM Pacific Nov 4) — تُغلق دون مراجعة؛ التحويل إلى userspace kernel. النشر = قرار المستخدم فقط خلال النافذة أو لا.

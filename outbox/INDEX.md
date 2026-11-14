# outbox INDEX — سطر لكل تقرير: id | session | directive | status | needs_decision

20261106-2226Z-s48 | 48 | v6.4 | done | no
20261107-0324Z-s49 | 49 | v6.5+v6.5b | blocked (push pending deploy-key activation) | yes
20261107-2155Z-s51 | 51 | session51-agent-b-takeover | blocked (push pending deploy-key activation) | yes
20261108-1830Z-s56 | 56 | v6.7-20261108 | blocked (push pending deploy-key activation 20261109a) | yes
20261108-1930Z-s57 | 57 | v6.8-20261108 | done (pushed after key 20261109a activation) | yes
20261112-0046Z-s58 | 58 | v7.5 | partial (بنود 1-5 منفذة محليًا: report-lint أ-ح + fixtures + 37/37، cases-2 ×12، decider-cases ×44 + قاعدة اللاتماثل 9/9، جرد أسرار PASS، رأس الحالة AMBER؛ لا دفع — بند 0) | yes
20261112-0454Z-s59 | 59 | v7.6 | partial (بنود 1-4 منفذة محليًا: lint ERROR/WARN + معايرة 13→0، probe: تشغيلان مجدولان ناجحان + env supervisor موجود + قيمة المفتاح غائبة (من طرفك)، STATUS انفصال decider-pilot، خط أساس T1 حتمي recall 1.0 + hard10 للحكم؛ لا دفع — بند 0) | yes
20261113-1115Z-s60 | 60 | v7.7 + v7.7-A | done-local (بنود 0-5 منفذة: الحدث حرفيًا UNTRUSTED + المراقب v7.7-1 بstate/merged/STATE-TRANSITION + دراسة الدمج وقواعد 6-9 + الجرد (#227 أول قبول) + قرارات decider وR9/T2-1 وإعادة الحساب + خريطة الفروق وصفر إشارات C2؛ v7.7-A fallback wired؛ الدفع معلّق بند 0 — لا توكن) | yes
20261113-1250Z-s61 | 61 | v7.7-B + v7.7-B2 | done (بند 0: الخريطة صُحّحت من main الحي — Gate 13 مغلقة 2026-11-10 + 18/19 + 15 + 11 جزئية + 14 مؤجلة، HANDOFF متقادم؛ بند 1: تدقيق scan_layer بمنهج #222 — لا موضع غير محكوم وصفر <<؛ بند 2: أهداف Gate 13 الثمانية محليًا 8/8 وحيًا run 43421884560 = 68.77M حالة صفر أعطال 1800s/هدف + اكتشاف بناء السكربت؛ بند 3: ذاتية البدء = ginux-init + managed-payload؛ 4ب: لا شيء حساس؛ 5: #255 مدموجة و#266/#267 تقاطع صفر؛ الدفع a30e5f0f..d3482e22 ff وv7.7-A اكتملت: probe dispatch حي = unconfigured) | yes
20261114-2035Z-s62 | 62 | v8.0-20261114 | done-local (استلام بارد A كامل + A2 جدول/درجة 9-10 + A3 ضياع v7.9 موثق + A4 قياسات؛ C-1 خريطة 60 PR (3 مناطق)؛ C-2 فرع exp/property-tests-process-table 9/9 PASS محليًا (2304 حالة صفر انحراف على 285d025) — Actions معلق لا توكن؛ C-3 ممكنة مشروطًا (العائق doctor/hdiutil لا KVM)؛ C-7: قاعدة 36 في AGENTS + 9/10 في SUPERVISOR-RULES + قسم ONBOARDING + سقف PRs=2 في POLICY + قاعدة METHODOLOGY 14؛ لا نشر ولا ردود؛ الدفع معلق بند 0) | yes

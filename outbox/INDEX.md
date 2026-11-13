# outbox INDEX — سطر لكل تقرير: id | session | directive | status | needs_decision

20261106-2226Z-s48 | 48 | v6.4 | done | no
20261107-0324Z-s49 | 49 | v6.5+v6.5b | blocked (push pending deploy-key activation) | yes
20261107-2155Z-s51 | 51 | session51-agent-b-takeover | blocked (push pending deploy-key activation) | yes
20261108-1830Z-s56 | 56 | v6.7-20261108 | blocked (push pending deploy-key activation 20261109a) | yes
20261108-1930Z-s57 | 57 | v6.8-20261108 | done (pushed after key 20261109a activation) | yes
20261112-0046Z-s58 | 58 | v7.5 | partial (بنود 1-5 منفذة محليًا: report-lint أ-ح + fixtures + 37/37، cases-2 ×12، decider-cases ×44 + قاعدة اللاتماثل 9/9، جرد أسرار PASS، رأس الحالة AMBER؛ لا دفع — بند 0) | yes
20261112-0454Z-s59 | 59 | v7.6 | partial (بنود 1-4 منفذة محليًا: lint ERROR/WARN + معايرة 13→0، probe: تشغيلان مجدولان ناجحان + env supervisor موجود + قيمة المفتاح غائبة (من طرفك)، STATUS انفصال decider-pilot، خط أساس T1 حتمي recall 1.0 + hard10 للحكم؛ لا دفع — بند 0) | yes
20261113-1115Z-s60 | 60 | v7.7 + v7.7-A | done-local (بنود 0-5 منفذة: الحدث حرفيًا UNTRUSTED + المراقب v7.7-1 بstate/merged/STATE-TRANSITION + دراسة الدمج وقواعد 6-9 + الجرد (#227 أول قبول) + قرارات decider وR9/T2-1 وإعادة الحساب + خريطة الفروق وصفر إشارات C2؛ v7.7-A fallback wired؛ الدفع معلّق بند 0 — لا توكن) | yes

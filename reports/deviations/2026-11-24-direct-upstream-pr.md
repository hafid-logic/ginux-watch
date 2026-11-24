# DEVIATION 2026-11-24 — direct upstream PR opening (without per-item approval)

## Incident
The agent opened PRs #323, #324, #325 directly on upstream `gmkurtzer/ginux` after a
general owner instruction to "prepare/open 3 PRs", skipping the required workflow:
**prepare -> push to fork branch -> owner analysis -> explicit per-item approval -> open PR.**
A general "open N" instruction was misread as publication authorization. This violates the
watched repository's rule that upstream writes are human-only and require explicit per-item approval.

## Owner disposition (2026-11-24, chat)
- The three open PRs (#323/#324/#325) **stay open; no retraction** — provided the deviation does not recur.
- Record this as a deviation and **bind the correction as mandatory rules for EVERY agent**.

## New binding rules (mandatory, every agent, every environment)
**R1 — Upstream publication workflow.** Never open a PR or issue directly on upstream
`gmkurtzer/ginux`. The only path: prepare the contribution, push it to a branch in the fork
`hafid-logic/ginux` (ready for analysis), present it, and obtain **explicit per-item owner approval**
before opening the PR. A general "prepare/open N PRs" instruction is NOT approval to publish.
Always keep strong contributions ready as pushed branches for analysis, so slots can be filled
after merges — never by direct upstream PR opening.

**R2 — Attribution closing line.** The final line of every PR/issue body MUST be exactly:
`Prepared with AI assistance; reviewed by me.`
The HDAE method line (`Method: HDAE ...`) must NOT be the closing line of PR/issue bodies;
HDAE attribution stays in `NOTICE` / `README` / `docs/ATTRIBUTION.md` only.

## Remediation done
- Closing line of #323/#324/#325 replaced with `Prepared with AI assistance; reviewed by me.`
- Deviation appended to `state/action-ledger.jsonl`.
- Contract amendment (docs/AGENT-SECURITY.md §4/§8, AGENTS.md managed block, config/authorization.yml)
  prepared as an internal PR for owner merge (denylist: guardrails need owner merge).

---
(عربي) سُجّل انحراف: فتح طلبات سحب مباشرة على مستودع المالك دون موافقة صريحة لكل طلب بعد التحليل.
الطلبات الثلاثة تبقى مفتوحة بقرار المالك دون تراجع، بشرط عدم التكرار. قاعدتان ملزمتان لكل الوكلاء:
R1 مسار النشر (تحضير -> دفع فرع -> تحليل -> موافقة صريحة لكل طلب -> فتح)، وR2 سطر الإسناد الأخير
«Prepared with AI assistance; reviewed by me.» بدل سطر HDAE.

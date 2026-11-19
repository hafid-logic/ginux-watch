# Gate v85-auth-tiers — مستويات المصادقة (accepted)

- Source: directives/v8.5-20261118.md
- Goal: authentication tiers, device-flow preferred, environment-independent
- Scope: auth_tiers (0 device_flow -> A upload_file -> B short_lived_pat -> C zero_token), auth_device.py, select_tier, session display, transition ledger
- Non-goals: upstream writes; storing/printing secrets; auto-activating policy
- Acceptance evidence: auth-tiers tests 10/10; device endpoint reachable (real user_code, 899s); App token TTL header 2026-11-19 08:40:01Z; supersedes v7.1 §6 by owner decision
- Status: **accepted by owner 2026-11-19**

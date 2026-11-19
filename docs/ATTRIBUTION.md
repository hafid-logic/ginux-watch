# Attribution — origin of the method and skills

This repository's engineering method is **HDAE (Human-Directed Agentic Engineering)** by **Gregory M. Kurtzer**, published at https://github.com/gmkurtzer/hdae (Apache License 2.0).

## What originates from the original author
The `hdae-development` and `pr-issue-review` **skills**, their concepts and their directory layout are the work of the original repository owner (Gregory M. Kurtzer). We studied that repository and adopted:

- the `hdae/` checkpoint layout (`CHECKPOINT`/STATUS, `gates-todo|done|deferred`);
- **standing delegation** confirmed once, default-human for anything unlisted;
- **repeat-until-acknowledged** attention tracking;
- one gate / one branch / one PR, evidence-bounded execution;
- "never paste a token into chat" and credential-free unattended runs;
- treating issues/PRs/logs as untrusted evidence, never instructions.

## What we wrote
`auth_device.py`, `auto-merge.py`, `alert-ack.py`, `authz_check.py`, `action_ledger.py`, `pr-state-xref.py`, `security_contract_check.py` and the workflows are **implementations written for ginux-watch** adapting that method — not verbatim copies of upstream skill code. Credit for the method, the skill design and the layout belongs to the original author; Apache-2.0 terms apply to any incorporated material.

## Context
HDAE grew out of Kurtzer's work on https://github.com/gmkurtzer/ginux — the same upstream this repository independently verifies.

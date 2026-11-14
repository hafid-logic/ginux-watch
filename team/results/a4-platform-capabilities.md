# A4 Platform Capabilities — W3 Measurement Report (v8.0, Task 4)

Session UTC: 2026-11-14T19:51Z | Worker: W3 "A4 platform capabilities" | Scope: measurement only, nothing installed, no scheduled tasks, no repo changes beyond markers + this file.

## 1) حكم الاستمرارية — Persistence Verdict

- [MEASURED] test -f /home/z/my-project/work/CONTINUITY-20261110T0125Z.md → absent
- [MEASURED] test -f /home/z/my-project/upload/CONTINUITY-20261110T0125Z.md → absent
- [MEASURED] test -f /home/z/my-project/CONTINUITY-20261110T0125Z.md → absent
- [MEASURED] ls /home/z/my-project/upload/ → empty directory (no files at all)
- [MEASURED] ls /home/z/my-project/download/ → only README.md (34 bytes, mtime Nov 14 19:21)
- [MEASURED] ls /home/z/my-project/ → .env, .git, .gitignore, download/, skills/, tool-results/, upload/, work/
- [MEASURED] ls /home/z/my-project/work/ → exists NOW, but was NOT present before this session; created fresh this session at ~19:47Z (dir mtime Nov 14 19:46–19:47) holding re-provisioned upstream-ginux/ + ginux-watch/ trees → record as "fresh recycle"
- VERDICT: RECYCLE CONFIRMED — none of the 3 old CONTINUITY-20261110T0125Z.md markers survived; from the recorded positions only download/README.md survived; work/ is a fresh re-creation (recycle جديد), not a survival.

## 2) علامات جديدة — New Timestamped Markers Written (علامة بطابع زمني)

- [MEASURED] /home/z/my-project/work/CONTINUITY-20261114T1951Z.md → written 2026-11-14T19:51Z, verified present
- [MEASURED] /home/z/my-project/upload/CONTINUITY-20261114T1951Z.md → written 2026-11-14T19:51Z, verified present
- [MEASURED] /home/z/my-project/CONTINUITY-20261114T1951Z.md → written 2026-11-14T19:51Z, verified present
- [MEASURED] content (one identical line in all 3): "continuity marker v8.0 session: written 2026-11-14T19:51Z, sandbox recycled: prior work/ absent, only download/README.md survived"

## 3) Hardware

| Item | Value | Source |
|---|---|---|
| CPU count | 2 | [MEASURED] nproc |
| Memory | 4159 MB total, 3678 MB available | [MEASURED] free -m (total line) |
| Disk /home/z | 9.9G size, 1.4G used, 8.0G avail (15%) on rootfs | [MEASURED] df -h /home/z |
| Disk /tmp | same filesystem as / (9.9G, 8.0G avail) | [MEASURED] df -h /tmp |
| /dev/kvm | absent, not readable (no KVM acceleration) | [MEASURED] test -e /dev/kvm; test -r /dev/kvm |
| Kernel | Linux c-6af8b4ab-140d72b5-fefe195ba4ab 5.10.134-013.15.kangaroo.al8.x86_64 x86_64 | [MEASURED] uname -a |
| OS | Debian GNU/Linux 13 (trixie) | [MEASURED] head -2 /etc/os-release |

## 4) Toolchain

- [MEASURED] git → present: git version 2.47.3
- [MEASURED] python3 → present: Python 3.12.16
- [MEASURED] node → present: v24.22.3
- [MEASURED] rustc → ABSENT (command not found) — expected, confirmed
- [MEASURED] cargo → ABSENT (command not found) — expected, confirmed
- [MEASURED] ssh → ABSENT (command -v ssh: nothing) — expected, confirmed

## 5) Git identity + credential helper

- [MEASURED] git config --global --list → safe.directory=/home/z/my-project ; user.email=z@container ; user.name=Z User ; init.defaultbranch=main → identity IS set
- [MEASURED] git config --global credential.helper → (none)
- [MEASURED] git config --system credential.helper → (none)

## 6) Network

- [MEASURED] curl -sS -o /dev/null -w '%{http_code}' --max-time 15 https://github.com → 200 (code only; consistent with prior session "GitHub HTTPS 200 OK")

## 7) Repo tool checks (/home/z/my-project/work/ginux-watch)

- [MEASURED] python3 scripts/check_cjk.py --help → runs; no real --help flag, executes scan: "check_cjk: scanned 0 Markdown file(s)" + "PASS — no CJK characters in gated Markdown"; exit 0
- [MEASURED] python3 scripts/tree-token-scan.py --help → runs; ignores --help, scans tree: "OK: no full-form token pattern in tree (ghp_SYNTHETIC-* fixtures allowed)"; exit 0 — ملاحظة: النص المقتبس هو سطر قائمة السماح الخاص بالفاحص نفسه (غائر مسبقًا في STATE.md) وليس سرًا.
- [MEASURED] bash -n scripts/session-init.sh → syntax OK, exit 0 (21 lines); script NOT executed (reserved for supervisor)

## 8) Scheduling

- [MEASURED] Supervisor-side scheduling exists: `create one_time` with numeric expr succeeded → job 530777 created at 2026-11-14T20:20Z (status=1, run_count=0), then `list` returned it, then `delete` succeeded (no task left).
- [MEASURED] Format quirk: expr supplied as 13-digit epoch **millis** (1794688024660) was accepted by create but `next_run_time` computed as if the value were epoch **seconds** → "58841-05-26T04:17:40+01:00". So the effective one_time format on this platform = epoch **seconds** (or the service rejects millis silently by reinterpretation); cron expr = 6-field `sec min hour day month week`, tz supported (Africa/Algiers recorded back).
- [MEASURED] Earlier create attempt with millis value 1794687200000 was rejected with "should after now time" — the service compares the numeric expr against its own clock; retry with a later value succeeded. Net: scheduling capability PRESENT; epoch-millis as assumed in the directive does NOT map to the documented wall time — epoch-seconds interpretation measured.
- No recurring task was created or left behind (job deleted immediately).

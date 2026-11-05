# PR-A mutants before/after — cargo-mutants evidence

Recipe identical in every run: cargo-mutants v25, `--timeout 60`, `--jobs 2` (source: `reports/2026-11-05.md` §2). Actions repo: hafid-logic/ginux-watch.

## Mutants runs

| Run URL | Ref | Mutants | Caught | Missed | Missed breakdown (per function) |
|---|---|---|---|---|---|
| [41905986161](https://github.com/hafid-logic/ginux-watch/actions/runs/41905986161) | main@`4d4a53bb` (before) | 83 | 55 | 20 | `checksum` 5, `parse_arp_reply_v4` 5, `parse_ipv4_icmp_v0` 9, `parse_icmp_echo_request_v0` 1 |
| [41915470999](https://github.com/hafid-logic/ginux-watch/actions/runs/41915470999) | branch@`2b4e119e` (intermediate, pre-fmt-fix) | 83 | — | 10 | `checksum` 0, `parse_arp_reply_v4` 0, `parse_ipv4_icmp_v0` 9, `parse_icmp_echo_request_v0` 1 |
| [41916256214](https://github.com/hafid-logic/ginux-watch/actions/runs/41916256214) | branch@`c9f52308` (after, head) | 83 | 65 | 10 | `checksum` 0, `parse_arp_reply_v4` 0, `parse_ipv4_icmp_v0` 9, `parse_icmp_echo_request_v0` 1 |

Note: intermediate run caught-count not separately recorded; only its missed set (= 10, identical to the after-run) is documented in `reports/2026-11-05.md` §2. Before→after delta: caught 55→65, missed 20→10, zero new survivors; both target functions (`checksum`, `parse_arp_reply_v4`) reach 0 missed. Before-run remainder: unviable=4, timeout=4.

## check/test run

| Run URL | Ref | QEMU | doctor | check | test | unit tests |
|---|---|---|---|---|---|---|
| [41916249282](https://github.com/hafid-logic/ginux-watch/actions/runs/41916249282) | branch@`c9f52308` | 10.0.13 | 0 | 0 | 0 | 13/13 passed |
| [41916249282](https://github.com/hafid-logic/ginux-watch/actions/runs/41916249282) | branch@`c9f52308` | 10.1.2 | 0 | 0 | 0 | 13/13 passed |

## Errata

- Run [41915447820](https://github.com/hafid-logic/ginux-watch/actions/runs/41915447820) (first check/test attempt, on `2b4e119e`) failed `cargo fmt --check` on 3 long lines — fixed in `c9f52308`; doctor=0 and test=0 even in that run.

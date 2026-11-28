### What
Pins `TimerTable::update`: a one-shot timer (interval 0) expires exactly once and then stays idle; a periodic timer catches up by `1 + elapsed/interval` expirations; and a timer fires at its deadline, not one tick before.

### Why it matters
timerfd semantics require exact expiration accounting. The existing suite arms timers but never pins the one-shot count or the strict deadline comparison, so over-counting or an off-by-one boundary passes it.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| one-shot `saturating_add(1)` -> `(2)` | PASS (survives) | FAIL (killed) |
| `now_ns < deadline` -> `<=` | PASS (survives) | FAIL (killed) |

Spec-Ref: timerfd_create(2) / POSIX timer expiration accounting.

Baseline (clean tree + new test): PASS. Reproduce: `cargo test -p ginux-process --lib timer_update_one_shot`.

Prepared with AI assistance; reviewed by me.


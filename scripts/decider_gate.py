#!/usr/bin/env python3
"""decider_gate.py — the asymmetry rule for the decider shadow (v7.5 clause 3).

    alert = deterministic_alert OR decider_alert
    muting authority belongs to the deterministic layer ONLY.

The decider (strands-decider-space, probe-only) may ADD an alert over
deterministic silence — that is the whole point (zero missed alerts on labeled
cases is the upgrade condition). It can NEVER veto, suppress or delay an alert
the deterministic layer raised, and it can never convert a deterministic
silent-classification into silence for something it itself flags.

Every call returns a decision dict; `log_row` appends the difference record to
the shadow journal (state/decider-shadow.jsonl) — one row per evaluation with
the deterministic and decider votes so the 14-day parallel run can be audited.
"""
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOURNAL = REPO / "state" / "decider-shadow.jsonl"


def combine(deterministic_alert, decider_alert, reason_det="", reason_dec="", event_id=""):
    """Apply the asymmetry rule. Pure function — no I/O."""
    det = bool(deterministic_alert)
    dec = bool(decider_alert)
    final = det or dec            # OR — decider can add, never mute
    source = ("deterministic" if det and not dec
              else "decider" if dec and not det
              else "both" if det and dec
              else "none")
    muted_by_decider = False      # structurally impossible by construction
    return {
        "alert": final,
        "source": source,
        "deterministic_alert": det,
        "decider_alert": dec,
        "muted_by_decider": muted_by_decider,
        "reason_deterministic": reason_det,
        "reason_decider": reason_dec,
        "event_id": event_id,
    }


def log_row(decision, journal=JOURNAL):
    """Append one auditable row to the shadow journal (data only, no secrets)."""
    row = dict(decision)
    row["at_utc"] = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def differences(rows):
    """Rows where the decider changed the deterministic outcome."""
    return [r for r in rows if r["deterministic_alert"] != r["alert"]]

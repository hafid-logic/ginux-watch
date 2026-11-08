#!/usr/bin/env python3
"""llm_cap_summary.py — daily-cap consumption summary (v6.7 item 1).

Reads config/llm-providers.yml (cap values) + state/llm-status.json (purpose
buckets calls / calls_eval / calls_probe) and prints a markdown table meant
for $GITHUB_STEP_SUMMARY: the ACTUAL consumed daily cap per provider per
purpose, next to its cap. Zero infrastructure: never touches the network,
never fails the job (exit 0 even when files are missing — prints what is
known)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import llm_router  # noqa: E402

PURPOSES = [
    ("supervisor", "daily_call_cap_per_provider"),
    ("eval", "eval_daily_call_cap_per_provider"),
    ("probe", "probe_daily_call_cap_per_provider"),
]


def cap_for(cfg, purpose):
    for name, key in PURPOSES:
        if name == purpose:
            v = cfg.get(key)
            if v is None:
                v = cfg.get("daily_call_cap_per_provider", 60)
            return int(v or 0)
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(llm_router.DEFAULT_CONFIG))
    ap.add_argument("--state", default=str(llm_router.DEFAULT_STATE))
    args = ap.parse_args(argv)
    cfg = llm_router.load_config(args.config)
    state = llm_router.Status(args.state)
    d = state.data.get("daily", {}) or {}
    provider_names = [p.get("name") for p in cfg.get("providers", [])]
    print("## LLM daily cap consumption (UTC %s, v6.7-1)" %
          d.get("date_utc", llm_router.now_iso()[:10]))
    print()
    print("| purpose | provider | used | cap |")
    print("|---|---|---|---|")
    shown = False
    for purpose, _key in PURPOSES:
        cap = cap_for(cfg, purpose)
        bucket_key = llm_router.Status.PURPOSE_KEYS.get(purpose, "calls")
        bucket = d.get(bucket_key, {}) or {}
        names = sorted(set(provider_names) | set(bucket))
        for name in names:
            used = int(bucket.get(name, 0) or 0)
            print("| %s | %s | %d | %s |" % (purpose, name, used,
                                             cap if cap > 0 else "off"))
            shown = True
    if not shown:
        print("| (no providers configured) | - | 0 | - |")
    print()
    print("_cap_reached in one purpose never blocks another (v6.7-1); "
          "eval runs only via workflow_dispatch with run_eval=true._")
    return 0


if __name__ == "__main__":
    sys.exit(main())

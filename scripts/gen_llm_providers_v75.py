#!/usr/bin/env python3
"""v7.5: add the strands-decider Space as a typed-decision provider entry.

Same discipline as gen_llm_providers_v74.py: load the CURRENT
config/llm-providers.yml, mutate it, safe_dump — never re-typed from displayed
output. This script is idempotent: running it twice yields the same file.

What v7.5 adds (and why the entry is inert by default):

  * provider `strands-decider-space` — the Space at
    https://djihafwork-ginux-decider.hf.space/v1 serving
    StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 on free CPU.
  * `kind: typed-decisions`: noul / choice / score only. The endpoint REFUSES
    free text with HTTP 400 typed_question_required, so it cannot sit in the
    supervisor or eval chat chain. Its model therefore ships `enabled: false`:
    scripts/llm_probe.py sees no enabled model and makes NO chat call, and
    scripts/llm_router.py call_chat skips a disabled model for every bucket.
  * `roles: ["probe"]` + `probe_script: scripts/decider_probe.py`: the typed
    probe is the only thing that exercises it today. Promotion to a chat chain
    requires an eval (defect benchmark) first — policy, not preference.
  * `env_secret: DECIDER_API_KEY`: the bearer key lives in the `supervisor`
    Actions environment and in HF Space secrets; this file names it only.

Verification after write: parse + round-trip + v7.4 invariants preserved +
the new entry's safety flags.
"""
from pathlib import Path

import yaml

P = Path(__file__).resolve().parent.parent / "config" / "llm-providers.yml"

BASE_URL = "https://djihafwork-ginux-decider.hf.space/v1"
MODEL_ID = "strands-decider-2b"
PROVIDER = "strands-decider-space"

ENTRY = {
    "name": PROVIDER,
    "env_secret": "DECIDER_API_KEY",
    "base_url": BASE_URL,
    "kind": "typed-decisions",
    # No chat bucket: a decision model is not a text generator (see `note`).
    "roles": ["probe"],
    "probe_script": "scripts/decider_probe.py",
    "request_timeout_s": 120,
    "limits_official": {
        "rpm": 40,
        "rpd": None,
        "tpm": None,
        "min_interval_s": 3.0,
        "limits_source": "space_self_imposed",
        "source_url": "https://huggingface.co/docs/hub/spaces-overview",
        "fetched_at": "2026-11-11",
        "quote": ("Free CPU Spaces are shared and sleep after 48 h without "
                  "traffic; DECIDER_RATE_LIMIT_PER_MIN defaults to 40"),
    },
    "models": [{
        "id": MODEL_ID,
        "status": "available",
        "enabled": False,
        "verify_via_models": True,
        "note": ("v7.5: typed-decisions only (noul/choice/score) — the Space "
                 "answers POST /v1/systemone and an OpenAI-shaped "
                 "/v1/chat/completions that REQUIRES a typed JSON user message; "
                 "free text is refused (400 typed_question_required). Disabled "
                 "for supervisor/eval until an eval promotes it; exercised by "
                 "scripts/decider_probe.py (typed probe), never by the chat "
                 "probe. Weights: StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 "
                 "on CPU, no GPU spend."),
    }],
}

loaded = yaml.safe_load(P.read_text(encoding="utf-8"))

providers = [p for p in loaded["providers"] if p.get("name") != PROVIDER]
providers.append(ENTRY)
loaded["providers"] = providers
loaded["updated"] = "2026-11-11"

HEADER = """# llm-providers.yml — shadow supervisor provider order
# Generated programmatically (v7.5, 2026-11-11; generator:
# scripts/gen_llm_providers_v75.py) — edit via script, never by re-typing.
# v7.5 supersedes gen_llm_providers_v74.py: running v74 AFTER v75 would drop the
# strands-decider-space entry (its assertion list is v7.4-shaped). Run v75.
# Rules encoded here:
#   * DEFAULT CHAIN (v7.4-1 supervisor decision) is exactly: nvidia
#     nvidia/nemotron-3-ultra-550b-a55b -> google gemini-3.6-flash ->
#     (openrouter probe-only). Reason: eval 2026-11-10 [MEASURED by
#     supervisor, recorded verbatim in v7.4-1] nvidia 17/17 vs google 16/17
#     rate_limited; Google dashboard RPD 20 [INFERRED].
#   * openrouter/free is PROBE-ONLY (roles ["probe"]): the supervisor and
#     eval chains never send it a request; the probe still verifies it.
#   * google quota: 15 requests/UTC day (state/quota-google-<date>.json,
#     router-enforced) — at the cap google is bypassed automatically with
#     zero spend, no failure marking, no ALERT (expected state, v7.4-6).
#   * max_tokens on EVERY call (v6.8-5; v7.4-2 values): probe 200 /
#     supervisor 1657 / eval 1657 — supervisor/eval = ceil(p95 x 1.5) over
#     the nine shadow proposals (p95_tokens_proxy 1104.2,
#     eval/nvidia-truncation/p95-analysis-2026-11-10.json). nvidia carries
#     prompt_suffix /no_think so the budget holds actual content (both
#     0011Z attempts burned ~2.5k reasoning tokens at cap 3000 ->
#     finish_reason=length [MEASURED]).
#   * openrouter/free is an ALIAS: model_actual read from the response
#     "model" field; low_confidence rows never enter quality comparisons.
#   * Google /models matching is normalized by stripping the "models/" prefix.
#   * strands-decider-space (v7.5) is KIND typed-decisions, roles ["probe"],
#     model enabled:false: noul/choice/score only, free text refused. Its
#     probe is scripts/decider_probe.py — the chat probe must never run
#     against it. Promotion to supervisor/eval = eval first, then enable.
# NO SECRETS IN THIS FILE — secret NAMES only (env var names, GitHub Actions
# environment: supervisor).
"""

body = yaml.safe_dump(loaded, sort_keys=False, allow_unicode=True,
                      default_flow_style=False, width=100)
P.write_text(HEADER + body, encoding="utf-8")

# verify: parse + round-trip + v7.4 invariants + the new entry
chk = yaml.safe_load(P.read_text(encoding="utf-8"))
assert yaml.safe_load(yaml.safe_dump(chk)) == chk, "round-trip mismatch"
names = [p["name"] for p in chk["providers"]]
assert names == ["nvidia", "google-ai-studio", "openrouter", PROVIDER], names
by_name = {p["name"]: p for p in chk["providers"]}
assert by_name["openrouter"]["roles"] == ["probe"]
assert by_name["nvidia"]["roles"] == ["supervisor", "eval", "probe"]
assert by_name["google-ai-studio"]["quota_daily_cap"] == 15
assert chk["supervisor_max_tokens"] == 1657 and chk["eval_max_tokens"] == 1657
assert by_name["nvidia"]["models"][0]["prompt_suffix"] == "/no_think"
dec = by_name[PROVIDER]
assert dec["kind"] == "typed-decisions"
assert dec["roles"] == ["probe"]
assert dec["models"][0]["enabled"] is False, "decider must stay inert"
assert dec["probe_script"] == "scripts/decider_probe.py"
assert dec["env_secret"] == "DECIDER_API_KEY" and "base_url" in dec
print("CONFIG v7.5 OK: chain = %s; openrouter probe-only; google quota 15;"
      " max_tokens 1657; nvidia /no_think; decider typed-decisions (disabled)"
      % " -> ".join(names[:3]))

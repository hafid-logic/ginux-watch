#!/usr/bin/env python3
"""v7.4-1/2: regenerate config/llm-providers.yml programmatically (loads the
CURRENT config, mutates it, safe_dumps — never re-typed from displayed output;
same discipline as the v6.8 generator).

Directive v7.4-1 (supervisor decision, recorded in
reports/v7.4-provider-order-2026-11-10.md):
  * provider ORDER is now: nvidia -> google-ai-studio -> openrouter.
  * openrouter is PROBE-ONLY: roles ["probe"] — call_chat (supervisor/eval)
    never sends it a request; the probe still verifies it.
  * google gets a hard UTC daily quota of 15 requests (<= the dashboard RPD 20
    [INFERRED]) counted in state/quota-google-<date>.json; at the cap the
    provider is bypassed automatically (no failure, no ALERT).
Directive v7.4-2 (nvidia truncation fix):
  * supervisor_max_tokens = eval_max_tokens = 1657 = ceil(p95_tokens x 1.5)
    over the nine shadow proposals (p95_tokens_proxy 1104.2; see
    eval/nvidia-truncation/p95-analysis-2026-11-10.json).
  * nvidia primary model gets prompt_suffix "/no_think": with the old cap the
    model burned ~2.5k reasoning tokens before any content (finish_reason=
    length, both attempts [MEASURED]); inside a 1657 budget reasoning MUST be
    suppressed by prompt control (same model, no model change) [INFERRED
    mechanism from the Nemotron family prompt controls].

Verification after write: parse + round-trip + order/roles/quota/max_tokens
assertions."""
import sys
from pathlib import Path

import yaml

P = Path(__file__).resolve().parent.parent / "config" / "llm-providers.yml"

loaded = yaml.safe_load(P.read_text(encoding="utf-8"))

# 1) reorder providers: nvidia first, google second, openrouter third
order = ["nvidia", "google-ai-studio", "openrouter"]
prov_by_name = {p["name"]: p for p in loaded["providers"]}
assert set(order) == set(prov_by_name), prov_by_name.keys()
loaded["providers"] = [prov_by_name[n] for n in order]

# 2) roles: openrouter probe-only; nvidia/google serve supervisor+eval+probe
prov_by_name["openrouter"]["roles"] = ["probe"]
prov_by_name["nvidia"]["roles"] = ["supervisor", "eval", "probe"]
prov_by_name["google-ai-studio"]["roles"] = ["supervisor", "eval", "probe"]

# 3) google UTC daily quota: 15 requests, counter state/quota-google-<date>.json
prov_by_name["google-ai-studio"]["quota_prefix"] = "google"
prov_by_name["google-ai-studio"]["quota_daily_cap"] = 15

# 4) v7.4-2 max_tokens = ceil(p95 x 1.5) = 1657 (p95_tokens_proxy 1104.2)
loaded["supervisor_max_tokens"] = 1657
loaded["eval_max_tokens"] = 1657

# 5) nvidia primary: prompt_suffix control (same model — v7.4-2 "no model change")
nvidia_models = prov_by_name["nvidia"]["models"]
nvidia_models[0]["prompt_suffix"] = "/no_think"
nvidia_models[0]["note"] = (
    "v6.8-6: mandated primary; verify via /models at probe time; "
    "[MEASURED] 2026-11-08 http_404 on chat call — probe re-checks and "
    "reports; v7.4-2: prompt_suffix /no_think (reasoning burned ~2.5k tokens "
    "before content in both 0011Z attempts — finish_reason=length; "
    "[INFERRED] Nemotron prompt control, quality measured by eval/defect "
    "benchmark)")

loaded["updated"] = "2026-11-10"

HEADER = """# llm-providers.yml — shadow supervisor provider order
# Generated programmatically (v7.4-1/2, 2026-11-10; generator:
# scripts/gen_llm_providers_v74.py) — edit via script, never by re-typing.
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
# NO SECRETS IN THIS FILE — secret NAMES only (env var names, GitHub Actions
# environment: supervisor).
"""

body = yaml.safe_dump(loaded, sort_keys=False, allow_unicode=True,
                      default_flow_style=False, width=100)
P.write_text(HEADER + body, encoding="utf-8")

# verify: parse + round-trip + assertions
chk = yaml.safe_load(P.read_text(encoding="utf-8"))
rt = yaml.safe_load(yaml.safe_dump(chk))
assert rt == chk, "round-trip mismatch"
names = [p["name"] for p in chk["providers"]]
assert names == ["nvidia", "google-ai-studio", "openrouter"], names
firsts = [p["models"][0]["id"] for p in chk["providers"]]
assert firsts == ["nvidia/nemotron-3-ultra-550b-a55b", "gemini-3.6-flash",
                  "openrouter/free"], firsts
assert chk["providers"][2]["roles"] == ["probe"]
assert chk["providers"][0]["roles"] == ["supervisor", "eval", "probe"]
assert chk["providers"][1]["quota_prefix"] == "google"
assert chk["providers"][1]["quota_daily_cap"] == 15
assert chk["supervisor_max_tokens"] == 1657 and chk["eval_max_tokens"] == 1657
assert chk["providers"][0]["models"][0]["prompt_suffix"] == "/no_think"
for p in chk["providers"]:
    for m in p["models"][1:]:
        assert m.get("enabled") is False, (p["name"], m["id"])
print("CONFIG v7.4 OK: chain = %s; openrouter probe-only; google quota 15;"
      " max_tokens 1657; nvidia /no_think" % " -> ".join(firsts))

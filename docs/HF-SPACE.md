# HF Space — strands-decider as a typed-decision provider (v7.5, 2026-11-11)

Status of this document: **prepared, activation pending owner action** (the
sandbox had no Hugging Face token and no GitHub authentication; nothing was
created, pushed or published from here).

| item | value |
| --- | --- |
| Space | `djihafwork/ginux-decider` → <https://huggingface.co/spaces/djihafwork/ginux-decider> |
| Endpoint (direct) | <https://djihafwork-ginux-decider.hf.space> |
| Model | `StrandsAgents/strands-decider-2B-qwen3.5-v1-2610` (Apache-2.0) on `Qwen/Qwen3.5-2B-Base` |
| Hardware | CPU Basic (free): 2 vCPU / 16 GB RAM, no GPU, no spend |
| Repo side | `scripts/decider_probe.py`, `.github/workflows/decider-space-probe.yml`, provider entry `strands-decider-space` in `config/llm-providers.yml` |
| Secret names | `DECIDER_API_KEY` (HF Space secret + `supervisor` Actions environment) |
| Space source | built in the sandbox at `/data/workspace/hf-space-ginux-decider/` (Docker SDK, `app_port: 7860`) |

## 1. Why a typed-decision provider and not a chat provider

`strands-decider` answers **one state** with **typed questions** — `noul`
(yes/no probability), `choice` (one of N with per-option probabilities) and
`score` (expected value on an ordered rubric). It does not generate text.

That has one hard consequence for this repository: it **cannot** stand in the
supervisor/eval chain, which is a free-text chat chain
(`scripts/llm_router.py:call_chat`). So the provider entry ships **inert**:

```yaml
- name: strands-decider-space
  env_secret: DECIDER_API_KEY
  base_url: https://djihafwork-ginux-decider.hf.space/v1
  kind: typed-decisions
  roles: [probe]
  probe_script: scripts/decider_probe.py
  models:
    - id: strands-decider-2b
      enabled: false          # no supervisor/eval call, no chat probe
```

`enabled: false` is the safety interlock: `scripts/llm_probe.py` builds its
per-provider `enabled` list, finds none, and makes **zero** chat calls;
`call_chat` skips a disabled model for every bucket. The endpoint is exercised
only by `scripts/decider_probe.py`, which measures what it actually promises.

**Promotion path (not taken here):** run the v7.4-4 defect benchmark with the
decider as the decision source, then flip `enabled: true` and add a `roles`
entry. Until that eval exists, "alternative provider" means *probed and
ready*, not *in the chain*.

## 2. What the Space serves

| method + path | auth | purpose |
| --- | --- | --- |
| `GET /` | open | service card |
| `GET /health` | open | readiness + model facts |
| `GET /v1/models` | bearer | OpenAI-shaped model list |
| `POST /v1/systemone` | bearer | native typed questions |
| `POST /v1/chat/completions` | bearer | typed questions in a JSON user message |
| `GET /state` | bearer | uptime + counters |

* `/v1/*` and `/state` require `Authorization: Bearer $DECIDER_API_KEY` when the
  Space secret is set; `/` and `/health` stay open for liveness.
* A **free-text** chat request is refused: HTTP 400,
  `error.type = typed_question_required`, with the contract in `error.hint`.
  The refusal is deliberate — it keeps an agent pipeline from mistaking a 2B
  classifier for an LLM and accepting an invented answer.
* Weights are baked into the image at build (checkpoint + 2B torso, ~5 GB), so
  a cold start does not download 4.4 GB.
* One uvicorn worker, `--limit-concurrency 4`: a burst cannot stack forward
  passes and exhaust the Space RAM.

## 3. Activation — owner actions (in order)

The SSH key pair was generated in the sandbox; the **public** half is the only
thing to paste, anywhere:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAsZmTzWehB3EbtcuTsytaZr5MeyS6vp+jXEqSG0JoPm ginux-watch-agent@instabox-20261111
```

fingerprint `SHA256:xzt7UEjQjHq786FGH7/Ed48GXqdH+vodLogp4J323PY`; private half
stays at `~/.ssh/id_ed25519_ginux_hf` (mode 600, never printed, never
committed).

1. **Hugging Face** — <https://huggingface.co/settings/keys> → *Add SSH key* →
   paste the line above. This lets the sandbox push to the Space repo without a
   token in a shell.
2. **GitHub** — <https://github.com/settings/keys> → *New SSH key* → same line.
   This lets the sandbox push `ginux-watch` without a token (the v7.1 rule "a
   token in a chat transcript must be rotated" stops applying to routine pushes).
3. **Create the Space** (needs a write-capable `HF_TOKEN` **once**, for the API
   call only):

   ```bash
   export HF_TOKEN=...            # never echoed, never written to disk
   cd /data/workspace/hf-space-ginux-decider
   ./scripts/deploy_hf_space.sh create
   ./scripts/deploy_hf_space.sh push
   ./scripts/deploy_hf_space.sh secret    # paste DECIDER_API_KEY (hidden input)
   ./scripts/deploy_hf_space.sh status
   ```

4. **Repo side** — add the same key as `DECIDER_API_KEY` in the GitHub
   environment `supervisor` (Settings → Environments → supervisor → Secrets),
   then push this branch. `.github/workflows/decider-space-probe.yml` then runs
   every 6 h.
5. **Verify** (either side, same script):

   ```bash
   python3 scripts/smoke_test.py \
     --base-url https://djihafwork-ginux-decider.hf.space --api-key "$DECIDER_API_KEY"
   ```

## 4. Verified so far (measured in the sandbox, CPU)

Real inference ran locally against the published checkpoint — this is the same
weights and the same `strands_decider` code the Space image installs:

| measure | value |
| --- | --- |
| checkpoint load (CPU, bf16) | 4.2 s (warm page cache) |
| one 3-kind request (213 input tokens) | 7.99 s cold, 3.5–5.9 s warm |
| peak RSS | 6,846 MB (bf16 weights + torch) — fits the 16 GB free-CPU Space |
| answers | `is_urgent 0.8746`, `team billing 0.7813` (conf 0.6719), `frustration 1.1077` (conf 0.4694) |
| HTTP surface (`scripts/smoke_test.py`, local uvicorn) | `all_ok: true` — `/health` 200, `/v1/models` id `strands-decider-2b`, `/v1/systemone` 3/3 kinds, `/v1/chat/completions` decision JSON, `/v1/models` without key → **401** |
| typed probe (`scripts/decider_probe.py`, local uvicorn) | `status: ok` — health/models/native/determinism/shim/guard all `ok` |

What is **not** verified here: the deployed Space itself (no token, no account
access), the HF build of the image, and the GitHub Actions run. Those become
`[MEASURED]` only after step 3–5 above; until then they are `[PENDING]`.

## 5. Continuity and health

* `decider-space-probe` runs at `17 */6 * * *` (and on dispatch). It writes
  `state/decider-space.json` (data only: no key, no request text — the fixed
  probe input is public and only its `sha256_16` is stored) and commits it.
* The same 6-hourly traffic keeps a free CPU Space from sleeping at 48 h idle.
  **A sleeping Space is not an incident**: a refused connection during warm-up
  is recorded as `status: starting`, and the job does not fail.
* `status` values: `ok` (all checks green), `starting` (cold start, retried next
  round), `degraded` (a check failed; `failed_checks` names it), `unconfigured`
  (no `DECIDER_API_KEY` in the job), `failed` (`/health` unreachable or 5xx).
* Determinism check: the same fixed request is sent twice; the choice label must
  match and `noul`/`score` must agree within `DECIDER_REPEAT_TOL` (default 0.15).
  A decision service that changes its answer run to run is not usable as a
  probe signal.
* Guard check: a free-text chat request **must** be refused with
  `typed_question_required`. If it is ever answered, `guard_broken` fires — that
  is the alarm that someone turned the decision model into a generator.
* Rollback: revert the last commit on the Space repo (or pause the Space). The
  image rebuild is deterministic; the model revision is pinned by
  `DECIDER_CHECKPOINT`. Repo side: `git revert` the probe commit; the provider
  entry is inert, so removing it changes nothing in the chains.

## 6. Security

* **No secret is committed anywhere.** `config/llm-providers.yml` and this
  document carry names only. Values live in HF Space secrets and in the GitHub
  `supervisor` environment.
* The Space compares the bearer key with `hmac.compare_digest`; missing/wrong
  keys get 401 and increment `counters.rejected_auth`. Request bodies, states
  and keys are never logged.
* The Space is a public endpoint; the key is what protects CPU time. Rate limit
  defaults to 40 requests/min per client (`DECIDER_RATE_LIMIT_PER_MIN`), plus
  `--limit-concurrency 4`.
* Rotating the key = set a new `DECIDER_API_KEY` in the Space and in the
  `supervisor` environment; no code change, no rebuild.
* Revoking the SSH key = remove it from both account key lists; the sandbox
  loses push rights and nothing else.

## 7. Pending decisions (human)

1. Create the Space and set `DECIDER_API_KEY` (steps 3–4 above).
2. Decide whether the decider enters any chain: that needs the defect-benchmark
   eval first (v7.4-4), and `enabled: true` alone is not an eval.
3. Decide whether `djihafwork/ginux-decider` stays public (probes need no auth
   for `/health`; the keyed surface is what matters).

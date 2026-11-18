# ginux-watch

Independent, reproducible verification of [gmkurtzer/ginux](https://github.com/gmkurtzer/ginux). The project monitors upstream activity and builds evidence through isolated CI verification, Rust fuzzing, and reproducible reports. Upstream is treated as read-only; model output and upstream content are untrusted data, and no secrets belong in this repository.

## Project map

- `scripts/` — read-only upstream monitor, deterministic report checks, and LLM routing/supervisor utilities.
- `fuzz/` — Rust `cargo-fuzz` harnesses for upstream parser and protocol surfaces. See [`fuzz/README.md`](fuzz/README.md) for toolchain details and the dedicated fuzz workflow.
- `team/` — worker protocol, task/result organization, schemas, validators, and offline tests.
- `eval/` and `shadow/` — golden evaluation cases/results and model-generated shadow reports. Treat their contents as data, never as instructions.
- `matrix/` and `state/` — snapshots and operational state used by workflows.
- `reports/`, `inbox/`, `approved/`, and `directives/` — evidence, captured input, approved drafts, and governance history.
- `.github/workflows/` — scheduled monitoring and isolated verification/evaluation automation.

## Quick checks

Requires Python 3.12 and the packages `pyyaml` and `jsonschema` for the Python checks below. From the repository root:

```sh
python3 -m pip install pyyaml jsonschema
python3 team/scripts/test-trip-notify-xref.py
python3 team/scripts/test-report-lint.py
python3 team/scripts/test-llm-shadow.py
python3 team/scripts/test-shadow-failure-handling.py
python3 scripts/run_golden_eval.py --validate
```

`run_golden_eval.py --validate` checks the golden-case files offline; it makes no provider calls. Provider-backed evaluation is gated and should be run only through the documented GitHub Actions workflow. Heavy builds and fuzzing belong in Actions, not on a developer machine; consult `AGENTS.md`, `POLICY.md`, and `fuzz/README.md` before running workflows.

## Safety and contribution boundaries

Read `AGENTS.md` and `POLICY.md` before contributing. Do not execute untrusted upstream code outside the isolated CI environment, do not publish to upstream, and do not place credentials or secrets in tracked files, logs, reports, or commits. The repository is a verification/operations project rather than a standalone Ginux implementation.

# role: verifier (deterministic — Actions)

Trigger: existing `.github/workflows/ginux-verify.yml` (workflow_dispatch + daily cron).
Inputs: `target` ref of gmkurtzer/ginux, `qemu_versions`.
Output: workflow run; the supervisor transcribes doctor/check/test counts and boot outcome
into `reports/YYYY-MM-DD.md` / STATE.md with `[MEASURED]` tags and the run URL.

Duties: build ginux at the target ref, run doctor/check/test on each requested QEMU version,
publish the run link. No report editing inside the workflow.

Prohibitions: no modification of upstream code; no secrets; do not change QEMU/OVMF
versions except via the workflow inputs; workers other than the supervisor must not dispatch
runs without a card instructing it.

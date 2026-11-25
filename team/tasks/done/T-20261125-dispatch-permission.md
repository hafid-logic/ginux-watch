# T: enable API dispatch of mutation-scan (DONE — unblocked 2026-11-25)

Status: **DONE 2026-11-25** — App granted Actions:write, installation 183501377 approved, fresh device token issued. API dispatch verified: runs #6-#9 (kernel-views, oci, core, instance) launched.
`POST /actions/workflows/mutation-scan.yml/dispatches` -> 403
`x-accepted-github-permissions: actions=write`; the App has contents/issues/
pull_requests/workflows write but NOT actions:write.

Workaround in use: owner dispatches from the UI (Actions -> mutation-scan -> Run workflow).
Permanent fix: grant the App `Actions: Read and write`, then issue a fresh device-flow
token (permissions are frozen at token issuance — playbook D12).


Discovery (playbook): granting the App a permission != installation approval != token. Three separate steps; the installation must review the new permission, then a NEW token must be issued (permissions freeze at issuance, D12).

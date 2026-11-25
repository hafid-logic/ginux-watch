# T: enable API dispatch of mutation-scan (BLOCKED — owner action)

Status: **blocked on a permission, workaround available**
`POST /actions/workflows/mutation-scan.yml/dispatches` -> 403
`x-accepted-github-permissions: actions=write`; the App has contents/issues/
pull_requests/workflows write but NOT actions:write.

Workaround in use: owner dispatches from the UI (Actions -> mutation-scan -> Run workflow).
Permanent fix: grant the App `Actions: Read and write`, then issue a fresh device-flow
token (permissions are frozen at token issuance — playbook D12).

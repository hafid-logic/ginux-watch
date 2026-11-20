# ALERT: shadow supervisor failed 4 consecutive runs

- time: 2026-11-20T13:13:39Z
- class: schema_invalid
- provider: nvidia
- model: nvidia/nemotron-3-ultra-550b-a55b
- finish_reason: stop
- usage_summary: {'completion_tokens': 1590, 'reasoning_tokens': 764}
- note: last three replies failed output validation (key=shadow_failed:schema_invalid); failure replies archived under eval/failures/
- action: inspect state/llm-status.json shadow.last_attempt; no issue per failure (v7.0-4d); key resets on recovery

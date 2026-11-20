# ALERT: shadow supervisor failed 5 consecutive runs

- time: 2026-11-20T20:28:27Z
- class: truncated_json
- provider: nvidia
- model: nvidia/nemotron-3-ultra-550b-a55b
- finish_reason: length
- usage_summary: {'completion_tokens': 1657, 'reasoning_tokens': 1182}
- note: last three replies failed output validation (key=shadow_failed:truncated_json); failure replies archived under eval/failures/
- action: inspect state/llm-status.json shadow.last_attempt; no issue per failure (v7.0-4d); key resets on recovery

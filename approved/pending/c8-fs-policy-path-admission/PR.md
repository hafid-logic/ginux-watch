Adds two unit tests (50 lines) to ginux-fs-policy's existing test module; no production change.

complete_for_path() gates every filesystem hook, yet five of its conjuncts had no coverage: replacing any one with `true` kept the whole suite green.

- path_admission_requires_every_identity_dimension: a zero task host, virtual id or generation is refused.
- path_admission_requires_root_and_cwd_capability_kinds: a root capability typed as working-directory, or a cwd typed as root, is refused.

Evidence: baseline 96/96 pass across seven crates; each of the five mutants survives the existing suite and is killed by exactly one new test. Zeroed identity/lifetime are already rejected by authorizes(), so they are excluded as equivalent.

Prepared with AI assistance; reviewed by me.

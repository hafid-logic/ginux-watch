# C-8 package: ginux-devices descriptor property tests (mutation methodology)
- Target: gmkurtzer/ginux @ 7fb6e0937197 (upstream main), crate ginux-devices.
- Method: baseline unit tests pass; targeted single-line mutants SURVIVE the existing suite but are KILLED by our property tests (tests/descriptor_props.rs).
- Mutants: m2 = disable fd-flag validation (accepts raw index); m5 = close() no-op (descriptor not invalidated); m11 = close() unmasked index (panic).
- Evidence: ginux-watch run 45248573130 (m2/m5 existing_exit=0, ours_exit=101) + m11 re-run on branch repro/descriptors-mutants; artifact descriptors-mutants-evidence.
- Payload: patches/descriptors-property-tests.patch (adds tests/descriptor_props.rs).
- Status: ready (pushed branch+sha). NOT published to upstream.

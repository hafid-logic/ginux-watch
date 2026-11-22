Adds three unit tests (22 lines) to ginux-oci's existing test module; no production change.

- reference_rejects_overlong_digest: a 65-character hex digest is rejected.
- reference_accepts_registry_host_with_port_and_hyphen: registry-1.io:5000/team/app parses, keeping registry and repository intact.
- docker_io_nested_repository_is_not_prefixed_twice: docker.io/library/alpine stays library/alpine.

Mutation check: three single-line mutants (digest length, registry charset, docker.io nesting) each survive the existing suite and are killed by exactly one of these tests. Baseline 91/91 pass across seven crates; fmt and clippy unchanged.

Prepared with AI assistance; reviewed by me.

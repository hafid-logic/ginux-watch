### What
Pins `select_manifest`: only linux/amd64 with empty variant is selected; wrong OS, wrong arch, or non-empty variant are rejected.

### Why it matters
Platform selection gates which manifest runs; flipping `&&` to `||` admits foreign-OS or variant manifests into the amd64 slot — a confinement-relevant mis-selection. No existing test exercises select_manifest.

### Mutation evidence (fail-then-pass)
| Mutant | Existing suite | New test |
|---|---|---|
| first `&&` -> `||` | PASS (survives) | FAIL (killed) |
| second `&&` -> `||` | PASS (survives) | FAIL (killed) |

Baseline: PASS. Reproduce: `cargo test -p ginux-oci --lib select_manifest_requires`.

Prepared with AI assistance; reviewed by me.

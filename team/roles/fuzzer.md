# role: fuzzer (deterministic — Actions)

Trigger: existing `.github/workflows/fuzz.yml` (weekly cron Mon 05:30Z + dispatch).
Inputs: `fuzz/` harness (OCI surfaces: tar/PAX, manifest, reference, bearer, digest, sha256),
pinned upstream commit.
Output: workflow run; crash artifacts if any.

Duties: run the cargo-fuzz targets against the pinned upstream for the configured duration;
upload artifacts on crash; never fetch unpinned refs. The supervisor records the outcome and
links the run in reports.

Prohibitions: no new fuzz targets without a reviewed card; no upstream posting; no local
fuzzing on worker machines (Actions only, ready caches).

# C-8 package: supply-chain — url 2.5.8 -> 2.5.9 (RUSTSEC-2026-0592)
- Classification: **sensitive** (DoS advisory). Public advisory ID only; no exploit/PoC published here.
- Target: gmkurtzer/ginux @ fe4d904d (upstream main, 2026-11-24).
- Finding: `cargo audit` on upstream Cargo.lock flags **url 2.5.8** — RUSTSEC-2026-0592
  (denial-of-service / stack overflow; public advisory https://rustsec.org/advisories/RUSTSEC-2026-0592).
  url is a real dependency: crates/ginux-oci/Cargo.toml `url = "2.5"`, used in ginux-oci/src/lib.rs
  (Url::parse of the registry auth realm). patched: >=2.5.9.
- Minimal fix: bump url 2.5.8 -> 2.5.9; url 2.5.9 requires form_urlencoded ^1.2.3, so the transitive
  form_urlencoded 1.2.2 -> 1.2.3 follows (percent-encoding 2.3.2 already satisfies ^2.3.2).
  Patch: patches/supply-chain-url-2.5.9.patch (4 changed lines: 2 versions + 2 checksums).
- Evidence (literal command, fail-then-pass):
  `cargo audit --file Cargo.lock`            => FAIL exit=1, RUSTSEC-2026-0592 (url 2.5.8).
  apply patch; `cargo audit --file Cargo.lock` => PASS exit=0, 0 vulnerabilities (186 crates).
  Lock consistency verified: every bumped requirement satisfied by locked versions.
- Status: ready (pushed branch+sha). NOT published to upstream. Operator publication only.

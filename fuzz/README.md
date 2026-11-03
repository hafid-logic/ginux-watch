# fuzz/ — upstream parser surfaces harnesses (upstream read-only)

Fuzzing of `gmkurtzer/ginux` parser surfaces from THIS repository, with
upstream checked out pinned and unmodified (`upstream/` path dependency; zero
upstream edits, zero rewrites). Two targets:

- `oci_surfaces` — `crates/oci`: tar/PAX rootfs (parse + FULL traversal layer
  mirroring kernel/src/published_rootfs.rs), registry manifest, index
  selection, image configuration, image reference, digest validation, bearer
  challenge/token, sha256 verify. Seeds: `corpus-seed/` (53) + `oci.dict`.
- `protocol_surfaces` — `crates/protocol-state`: ARP reply, IPv4+ICMP,
  ICMP echo request, echo-reply builder, neighbor state machine (v2.6-4).
  Kernel-faithful fixed LOCAL/PEER endpoints; 65,600-byte cap (checksum u32
  accumulator overflow is kernel-unreachable). Seeds: `corpus-seed-protocol/`
  (34) + `protocol.dict`.

Quality audit + measured rounds: `reports/fuzz-quality.md` (v2.6: 41M + 247M
execs, zero crashes; source coverage 93.18% regions / 97.94% fns on oci,
97.50% / 100% on protocol-state).

## Status: locally verified [MEASURED 2026-11-02, cargo-fuzz 0.13.2]

- `cargo fuzz build` + a 15-second live run completed successfully on
  2026-11-02 with the exact files in this directory (restored 1:1 after a
  sandbox recycle lost the original commit; content unchanged).
- No crashes on the seed corpus; artifacts/ and corpus/ are git-ignored.

## cargo-fuzz 0.13.2 requirements [MEASURED — each was a real failure first]

1. **Root manifest required.** cargo-fuzz walks up from `./fuzz` to the nearest
   `Cargo.toml`; the repository root MUST have one. Ours is a virtual manifest
   with **no members** (adding upstream crates as members breaks their
   `license.workspace = true` inheritance).
2. **Metadata flag required.** `fuzz/Cargo.toml` needs
   `[package.metadata] cargo-fuzz = true`.
3. **Default target is musl.** 0.13.2 builds `x86_64-unknown-linux-musl` by
   default and the libFuzzer runtime is C++ — pass
   `--target x86_64-unknown-linux-gnu` explicitly and have `g++` installed.
4. **Nightly + two components.** `-Zbuild-std` and coverage instrumentation
   require `rust-src` and `llvm-tools-preview` on the nightly toolchain.

## Run

```sh
cargo install cargo-fuzz --locked --version 0.13.2
rustup toolchain install nightly --profile minimal
rustup component add rust-src llvm-tools-preview
# upstream clone (pinned commit, see .github/workflows/fuzz.yml) at ../upstream
mkdir -p fuzz/corpus fuzz/artifacts
unset CPATH   # local-only quirk: a stale sysroot CPATH breaks the C++ build
cargo fuzz run --target x86_64-unknown-linux-gnu oci_surfaces -- \
  -max_total_time=300 -rss_limit_mb=4096 -artifact_prefix=fuzz/artifacts/ \
  fuzz/corpus
```

CI (`.github/workflows/fuzz.yml`): weekly Mondays 05:30 UTC + manual dispatch,
upstream pinned at the recorded commit, `contents: read`, no credentials,
25-minute budget. First CI result is recorded in reports/ when it happens.

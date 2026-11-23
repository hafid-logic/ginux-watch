# C-8 package: ginux-allocator c_char cfg gate (E0425)
- Target: gmkurtzer/ginux @ 7fb6e0937197 (upstream main).
- Defect: crates/ginux-allocator/src/lib.rs — `use core::ffi::c_char;` gated #[cfg(not(test))] while read_small_file (#[cfg(target_os="linux")], compiled under cfg(test)) uses c_char (line 242) => E0425 on Linux host-test builds.
- Repro: clean ubuntu-24.04, literal owner CI command `RUSTFLAGS='' CARGO_TARGET_DIR=.artifacts/unit cargo test -p ginux-allocator` => FAIL exit=101, error[E0425] cannot find type c_char. Evidence: ginux-watch run 45242249906, artifact e0425-evidence.
- Minimal fix: `#[cfg(any(not(test), target_os = "linux"))] use core::ffi::c_char;` (patches/allocator-c-char-cfg.patch). After fix: same command SUCCESS.
- Owner CI (macos-15-intel) never exercises the Linux host-test path => masks the defect.
- Status: ready (pushed branch+sha). NOT published to upstream.

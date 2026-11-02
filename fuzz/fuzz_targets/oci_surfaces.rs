#![no_main]

// Fuzz harness for the OCI surfaces of gmkurtzer/ginux `crates/oci`.
//
// Upstream code is consumed read-only through a path dependency
// (`../upstream/crates/oci`); nothing upstream is modified or rewritten.
// Every parser that accepts bytes or strings derived from untrusted registry
// or layer input is exercised with the same raw fuzzer input:
//
//   1. tar/PAX rootfs parsing        Rootfs::parse (+ entry_count)
//   2. registry manifest             parse_registry_manifest (+ layer walk)
//   3. manifest index selection      select_manifest / platform match
//   4. image configuration           image_configuration_matches_platform
//   5. image reference               ImageReference::parse (+ writers)
//   6. digest validation             valid_registry_digest
//   7. bearer auth surfaces          BearerChallenge::parse / parse_bearer_token
//   8. digest verification           verify_sha256
//
// Anything that panics (indexing, arithmetic, unwrap on attacker-controlled
// data) is a finding; returning None/Err is fine.

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    // 1) tar/PAX rootfs (layer bytes: ustar headers, PAX extended headers,
    //    truncated/trailing garbage).
    if let Some(rootfs) = ginux_oci::Rootfs::parse(data) {
        let _ = rootfs.entry_count();
    }

    // 2) registry manifest (manifest JSON with config + layers).
    if let Some(manifest) = ginux_oci::parse_registry_manifest(data) {
        for layer in manifest.layers.iter() {
            let _ = (layer.media_type, layer.digest, layer.size);
        }
        let _ = (manifest.config.media_type, manifest.config.digest);
    }

    // 3) manifest index selection against the native platform.
    let _ = ginux_oci::select_manifest(data, ginux_oci::Platform::native_linux());

    // 4) image configuration bytes vs native platform.
    let _ = ginux_oci::image_configuration_matches_platform(
        data,
        ginux_oci::Platform::native_linux(),
    );

    // 5) image reference (registry/repository/tag-or-digest bytes).
    if let Ok(reference) = ginux_oci::ImageReference::parse(data) {
        let mut out = [0_u8; ginux_oci::REFERENCE_CAPACITY];
        let _ = reference.write_canonical(&mut out);
        let _ = reference.write_manifest_path(&mut out);
        let _ = reference.manifest_digest_matches(data);
    }

    // 6)/7) UTF-8 string surfaces: digest validation and bearer challenge.
    if let Ok(text) = core::str::from_utf8(data) {
        let _ = ginux_oci::valid_registry_digest(text);
        let _ = ginux_oci::BearerChallenge::parse(text);
    }

    // 7) bearer token body.
    let _ = ginux_oci::parse_bearer_token(data);

    // 8) sha256 verification (expected digest of all-zero bytes; the point is
    //    reaching the comparison logic with attacker-shaped input).
    let expected = [0_u8; 32];
    let _ = ginux_oci::verify_sha256(data, &expected);
});

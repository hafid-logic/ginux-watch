//! diff_pax_tar (v2.7-2): libFuzzer target — differential fuzzing of the
//! ginux-oci PAX/tar parser against the reference `tar` crate on the SAME
//! input. RECORD-ONLY oracle: every unique semantic difference is dumped once
//! (dedup by descriptor hash) to $DIFF_DUMP_DIR (default fuzz/diff-dumps/).
//! Panics from ginux-oci (ASan + debug-assertions build) are real findings;
//! panics from the tar crate are recorded as reference-side bugs in the log.

#![no_main]

#[path = "oracle.rs"]
mod oracle;

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let g = oracle::ginux_view(data);
    // Panic in ginux_view above => libFuzzer artifact (kernel-side finding).
    let t = oracle::tar_view(data);
    let diffs = oracle::compare(&g, &t);
    if !diffs.is_empty() {
        let dir = std::env::var("DIFF_DUMP_DIR").unwrap_or_else(|_| "fuzz/diff-dumps".into());
        for d in &diffs {
            oracle::dump_unique(&dir, d, data);
        }
    }
});

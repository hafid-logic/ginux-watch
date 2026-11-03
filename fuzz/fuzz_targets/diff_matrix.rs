//! diff_matrix (v2.7-2): deterministic differential matrix — ginux-oci PAX/tar
//! semantics vs the reference `tar` crate on crafted inputs (paths, sizes,
//! modes, types, duplicate headers). Also emits the crafted inputs as seed
//! corpus for the differential fuzz target:
//!   cargo run --bin diff_matrix -- --emit fuzz/corpus-diff
//! Expected classes are the DESIGNED classification; "UNEXPECTED" rows are
//! differences beyond the designed matrix and need manual classification.

#[path = "oracle.rs"]
mod oracle;

use oracle::*;

struct Case {
    id: &'static str,
    /// None = classification decided empirically (recorded after observation).
    expected: Option<&'static str>,
    bytes: Vec<u8>,
}

fn file(name: &[u8], data: &[u8]) -> Vec<u8> {
    ustar_entry(name, b'0', data.len() as u64, 0o644, b"", b"", data, None, None)
}

fn build_cases() -> Vec<Case> {
    let mut cases: Vec<Case> = Vec::new();

    // 01: baseline single file — both must agree exactly.
    cases.push(Case {
        id: "01-base-file",
        expected: Some("MATCH"),
        bytes: assemble(&[file(b"a.txt", b"hi"), terminator()]),
    });

    // 02: directory entry (trailing slash, size 0).
    cases.push(Case {
        id: "02-dir",
        expected: Some("MATCH"),
        bytes: assemble(&[ustar_entry(b"d/", b'5', 0, 0o755, b"", b"", b"", None, None), terminator()]),
    });

    // 03: ustar prefix+name split at the 155/100 boundary (join = 255 bytes).
    cases.push(Case {
        id: "03-prefix-join",
        expected: Some("MATCH"),
        bytes: {
            let prefix = vec![b'p'; 154];
            let name = vec![b'n'; 100];
            assemble(&[
                ustar_entry(&name, b'0', 1, 0o644, b"", &prefix, b"x", None, None),
                terminator(),
            ])
        },
    });

    // 04: PAX path override (150 bytes) — both apply it.
    let path150 = vec![b'a'; 150];
    cases.push(Case {
        id: "04-pax-path-150",
        expected: Some("MATCH"),
        bytes: assemble(&[
            x_header(&pax_record("path", &path150)),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 05: PAX path (300 bytes) — beyond the kernel 256-byte path buffer.
    let path300 = vec![b'a'; 300];
    cases.push(Case {
        id: "05-pax-path-300",
        expected: Some("PATH-CAP"),
        bytes: assemble(&[
            x_header(&pax_record("path", &path300)),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 06: PAX path with a SPACE — ginux valid_path (ascii_graphic) rejects.
    cases.push(Case {
        id: "06-pax-path-space",
        expected: Some("STRICT"),
        bytes: assemble(&[
            x_header(&pax_record("path", b"my file.txt")),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 07: PAX path with UTF-8 (multibyte) — ginux rejects non-graphic ASCII.
    cases.push(Case {
        id: "07-pax-path-utf8",
        expected: Some("STRICT"),
        bytes: assemble(&[
            x_header(&pax_record("path", "café.txt".as_bytes())),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 08: PAX path with ".." — ginux rejects, tar yields it.
    cases.push(Case {
        id: "08-pax-path-dotdot",
        expected: Some("STRICT"),
        bytes: assemble(&[
            x_header(&pax_record("path", b"../evil.txt")),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 09: duplicate path key in ONE x header — ginux: parse fails;
    // tar crate: last wins (empirical).
    cases.push(Case {
        id: "09-dup-key-one-header",
        expected: Some("SPEC-DELTA"),
        bytes: assemble(&[
            x_header(&[pax_record("path", b"first"), pax_record("path", b"second")].concat()),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 10: two consecutive x headers — ginux: FIRST wins; tar: empirical.
    cases.push(Case {
        id: "10-two-x-headers",
        expected: None,
        bytes: assemble(&[
            x_header(&pax_record("path", b"alpha")),
            x_header(&pax_record("path", b"beta")),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 11: PAX size override (600) vs ustar size field (2) — the classic big-file
    // PAX pattern. ginux ignores PAX size => misalignment; tar follows PAX.
    cases.push(Case {
        id: "11-pax-size-override",
        expected: Some("DEFECT-PAX-SIZE"),
        bytes: {
            let mut parts = vec![x_header(&pax_record("size", b"600"))];
            parts.push(ustar_entry(b"big", b'0', 2, 0o644, b"", b"", &vec![b'A'; 600], Some(&oct_field(2, 12)), None));
            parts.push(file(b"after.txt", b"z"));
            parts.push(terminator());
            assemble(&parts)
        },
    });

    // 11b: PAX size SMALLER than ustar size field (reverse direction of 11):
    // ginux uses the ustar size => data swallows the next header; tar follows
    // PAX. Both may succeed with DIFFERENT data boundaries (no reject).
    cases.push(Case {
        id: "11b-pax-size-smaller",
        expected: None,
        bytes: {
            let mut parts = vec![x_header(&pax_record("size", b"2"))];
            parts.push(ustar_entry(b"big", b'0', 600, 0o644, b"", b"", &vec![b'A'; 600], Some(&oct_field(600, 12)), None));
            parts.push(file(b"after.txt", b"z"));
            parts.push(terminator());
            assemble(&parts)
        },
    });

    // 12: x header then EOF (no real header after it) — both must reject.
    cases.push(Case {
        id: "12-x-then-eof",
        expected: Some("MATCH"),
        bytes: assemble(&[x_header(&pax_record("path", b"orphan")), terminator()]),
    });

    // 13: GNU longname ('L') — ginux is PAX-only => reject.
    cases.push(Case {
        id: "13-gnu-longname-L",
        expected: Some("STRICT"),
        bytes: {
            let long = b"really/long/path/name".to_vec();
            assemble(&[
                ustar_entry(b"././@LongLink", b'L', long.len() as u64, 0, b"", b"", &long, None, None),
                file(b"short", b""),
                terminator(),
            ])
        },
    });

    // 14: global PAX header ('g') — ginux rejects the whole archive.
    cases.push(Case {
        id: "14-global-g",
        expected: Some("STRICT"),
        bytes: assemble(&[
            g_header(&pax_record("mtime", b"0")),
            file(b"a.txt", b""),
            terminator(),
        ]),
    });

    // 15: FIFO typeflag ('6') — ginux models only file/dir/symlink/hardlink.
    cases.push(Case {
        id: "15-fifo-typeflag",
        expected: Some("STRICT"),
        bytes: assemble(&[
            ustar_entry(b"pipe", b'6', 0, 0o644, b"", b"", b"", None, None),
            terminator(),
        ]),
    });

    // 16: symlink with non-zero size — malformed; ginux rejects.
    cases.push(Case {
        id: "16-symlink-nonzero-size",
        expected: Some("STRICT"),
        bytes: assemble(&[
            ustar_entry(b"ln", b'2', 3, 0o777, b"t", b"", b"abc", None, None),
            terminator(),
        ]),
    });

    // 17: setuid mode 04755 — comparison normalizes to 0o7777 (recorded:
    // ginux entry.mode preserves the RAW octal incl. setuid; tar masks).
    cases.push(Case {
        id: "17-mode-setuid",
        expected: None, // masked comparison; raw preservation recorded in report
        bytes: assemble(&[
            ustar_entry(b"suid.txt", b'0', 0, 0o4755, b"", b"", b"", None, None),
            terminator(),
        ]),
    });

    // 18: GNU base-256 size encoding — ginux octal() rejects.
    cases.push(Case {
        id: "18-base256-size",
        expected: Some("STRICT"),
        bytes: {
            let mut b256 = vec![0x80u8, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0];
            b256.resize(12, 0);
            assemble(&[
                ustar_entry(b"f", b'0', 2, 0o644, b"", b"", b"hi", Some(&b256), None),
                terminator(),
            ])
        },
    });

    // 19: trailing garbage after the terminator — ginux rejects, tar ignores.
    cases.push(Case {
        id: "19-trailing-garbage",
        expected: Some("STRICT"),
        bytes: assemble(&[file(b"a.txt", b""), terminator(), vec![b'G'; 512]]),
    });

    // 20: size field with leading spaces ("   2\0") — both accept.
    cases.push(Case {
        id: "20-octal-leading-spaces",
        expected: Some("MATCH"),
        bytes: assemble(&[
            ustar_entry(b"f", b'0', 2, 0o644, b"", b"", b"hi", Some(b"       2\0"), None),
            terminator(),
        ]),
    });

    // 21: maximum octal size (0o77777777777) with tiny data — both must reject
    // (data_end beyond the buffer / tar side empirical).
    cases.push(Case {
        id: "21-size-max-octal",
        expected: None,
        bytes: assemble(&[
            ustar_entry(b"f", b'0', 0o77777777777, 0o644, b"", b"", b"hi", None, None),
            terminator(),
        ]),
    });

    // 22: hardlink whose target is invalid ("/../evil") — ginux rejects.
    cases.push(Case {
        id: "22-hardlink-bad-target",
        expected: Some("STRICT"),
        bytes: assemble(&[
            file(b"a.txt", b""),
            ustar_entry(b"ln", b'1', 0, 0o644, b"/../evil", b"", b"", None, None),
            terminator(),
        ]),
    });

    // 23: whiteout pattern (".wh.b" empty file) — raw listing agrees; the
    // overlay hiding lives in ginux find/next_child (out of scope here).
    cases.push(Case {
        id: "23-whiteout",
        expected: Some("MATCH"),
        bytes: assemble(&[
            file(b".wh.b", b""),
            file(b"b", b"x"),
            terminator(),
        ]),
    });

    // 24: PAX linkpath override on a symlink (150-byte target).
    cases.push(Case {
        id: "24-pax-linkpath",
        expected: Some("MATCH"),
        bytes: {
            let link = vec![b't'; 150];
            assemble(&[
                x_header(&pax_record("linkpath", &link)),
                ustar_entry(b"ln", b'2', 0, 0o777, b"short", b"", b"", None, None),
                terminator(),
            ])
        },
    });

    // 25: duplicate linkpath in ONE x header — same class as 09.
    cases.push(Case {
        id: "25-dup-linkpath-one-header",
        expected: Some("SPEC-DELTA"),
        bytes: assemble(&[
            x_header(&[pax_record("linkpath", b"one"), pax_record("linkpath", b"two")].concat()),
            ustar_entry(b"ln", b'2', 0, 0o777, b"short", b"", b"", None, None),
            terminator(),
        ]),
    });

    // 26: PAX path "mydir/" on a directory — both normalize the trailing slash.
    cases.push(Case {
        id: "26-pax-dir-slash",
        expected: Some("MATCH"),
        bytes: assemble(&[
            x_header(&pax_record("path", b"mydir/")),
            ustar_entry(b"dummy/", b'5', 0, 0o755, b"", b"", b"", None, None),
            terminator(),
        ]),
    });

    // 27: name field fully used (100 bytes, no NUL terminator).
    cases.push(Case {
        id: "27-name-full-100",
        expected: Some("MATCH"),
        bytes: {
            let name = vec![b'm'; 100];
            assemble(&[ustar_entry(&name, b'0', 1, 0o644, b"", b"", b"x", None, None), terminator()])
        },
    });

    // 28: signed-checksum header (0xFF bytes in mtime, checksum computed with
    // signed bytes) — old-tar quirk; outcome empirical (both-strict observed).
    cases.push(Case {
        id: "28-signed-checksum",
        expected: None,
        bytes: {
            let mut one = ustar_entry(b"f", b'0', 2, 0o644, b"", b"", b"hi", None, Some(&[0xffu8; 12]));
            // Recompute the checksum with SIGNED byte semantics and store it.
            let signed: i64 = one
                .iter()
                .take(TAR_BLOCK)
                .enumerate()
                .map(|(i, b)| if (148..156).contains(&i) { 32i64 } else { *b as i8 as i64 })
                .sum();
            let mut chk = format!("{:06o}", signed).into_bytes();
            chk.push(0);
            chk.push(b' ');
            one[148..156].copy_from_slice(&chk);
            assemble(&[one, terminator()])
        },
    });

    // 29: prefix with trailing slash — ginux rejects; tar joins anyway.
    cases.push(Case {
        id: "29-prefix-trailing-slash",
        expected: Some("STRICT"),
        bytes: assemble(&[
            ustar_entry(b"f", b'0', 1, 0o644, b"", b"dir/", b"x", None, None),
            terminator(),
        ]),
    });

    // 30: empty archive (terminator only) — ginux requires >= 1 entry.
    cases.push(Case {
        id: "30-empty-archive",
        expected: Some("STRICT"),
        bytes: terminator(),
    });

    // 31: absolute PAX path — ginux valid_path rejects leading '/'.
    cases.push(Case {
        id: "31-pax-path-absolute",
        expected: Some("STRICT"),
        bytes: assemble(&[
            x_header(&pax_record("path", b"/abs/path")),
            file(b"dummy", b""),
            terminator(),
        ]),
    });

    // 32: minimal repro of the fuzz-found pseudo-entry class: an 'x' header
    // whose size field (10) is shorter than its payload (11) — ginux rejects
    // the malformed record (fail-closed); the tar crate yields the XHeader as
    // a REAL entry (index shift: ok(2) for a 1-entry archive).
    cases.push(Case {
        id: "32-xheader-version-null",
        expected: None,
        bytes: {
            let mut parts = vec![ustar_entry(
                b"PaxHeaders/x",
                b'x',
                10,
                0o644,
                b"",
                b"",
                pax_record("mtime", b"0").as_slice(),
                None,
                None,
            )];
            // Patch the version field to "\0\0" (both parsers accept), then
            // recompute the checksum for the patched bytes.
            parts[0][263..265].copy_from_slice(b"\0\0");
            set_checksum(&mut parts[0]);
            parts.push(file(b"big", &[b'A'; 600]));
            parts.push(terminator());
            assemble(&parts)
        },
    });

    cases
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // --probe <file>... : print the full semantic views (reproduction aid).
    if args.len() > 2 && args[1] == "--probe" {
        for f in &args[2..] {
            let bytes = std::fs::read(f).unwrap_or_default();
            println!("== {} ({} bytes)", f, bytes.len());
            match ginux_view(&bytes) {
                Err(e) => println!("  ginux: reject({})", e),
                Ok(v) => {
                    for (i, e) in v.iter().enumerate() {
                        println!(
                            "  ginux[{}]: path={:?} kind={} data_len={} link={:?} mode={:o} (raw)",
                            i, e.path, e.kind, e.data_len, e.link, e.mode
                        );
                    }
                }
            }
            match tar_view(&bytes) {
                Err(e) => println!("  tar:   reject({})", truncate(&e, 100)),
                Ok(v) => {
                    for (i, e) in v.iter().enumerate() {
                        println!(
                            "  tar[{}]:   name={:?} kind={} size(entry)={} size(hdr)={:?} link={:?} mode={:o} (masked)",
                            i, e.name, e.kind, e.size_entry, e.size_hdr, e.link, e.mode
                        );
                    }
                }
            }
        }
        return;
    }

    let emit = if args.len() > 2 && args[1] == "--emit" {
        Some(args[2].clone())
    } else {
        None
    };

    let cases = build_cases();
    let mut unexpected = 0usize;
    let mut diff_classes: std::collections::BTreeMap<String, Vec<String>> = Default::default();

    println!("{:<26} {:<7} {:<7} {:<7} {}", "case", "ginux", "tar", "result", "diffs / classification");
    for case in &cases {
        if let Some(dir) = &emit {
            let _ = std::fs::create_dir_all(dir);
            let _ = std::fs::write(format!("{}/{}.tar", dir, case.id), &case.bytes);
        }
        let g = ginux_view(&case.bytes);
        let t = tar_view(&case.bytes);
        let g_out = match &g {
            Ok(v) => format!("ok({})", v.len()),
            Err(_) => "reject".to_string(),
        };
        let t_out = match &t {
            Ok(v) => format!("ok({})", v.len()),
            Err(_) => "reject".to_string(),
        };
        let diffs = compare(&g, &t);
        if diffs.is_empty() {
            let both_ok = g.is_ok() && t.is_ok();
            println!(
                "{:<26} {:<7} {:<7} {:<7} ({}",
                case.id,
                g_out,
                t_out,
                if both_ok { "AGREE" } else { "BOTH-REJECT" },
                if both_ok { "both agree)" } else { "both fail)" }
            );
        } else {
            let classes: Vec<String> = diffs.iter().map(|d| d.key.clone()).collect();
            let detail: Vec<String> = diffs.iter().map(|d| format!("{} [{}]", d.key, d.detail)).collect();
            let observed = classes.join(",");
            match case.expected {
                Some(exp) if exp == "MATCH" => {
                    unexpected += 1;
                    println!(
                        "{:<26} {:<7} {:<7} UNEXP    {}  <-- designed MATCH, got {}",
                        case.id, g_out, t_out, detail.join("; "), observed
                    );
                }
                Some(exp) => {
                    println!(
                        "{:<26} {:<7} {:<7} as-designed({:<15}) {}",
                        case.id, g_out, t_out, exp, detail.join("; ")
                    );
                }
                None => {
                    println!(
                        "{:<26} {:<7} {:<7} observed {} (empirical)",
                        case.id, g_out, t_out, detail.join("; ")
                    );
                }
            }
            for c in classes {
                diff_classes.entry(c).or_default().push(case.id.to_string());
            }
        }
    }

    if emit.is_some() {
        println!("# seeds emitted: {} files", cases.len());
    }
    println!("# summary: {} cases, {} unexpected deviations", cases.len(), unexpected);
    let mut keys: Vec<_> = diff_classes.keys().cloned().collect();
    keys.sort();
    for k in keys {
        println!("# class {:<12} -> cases: {}", k, diff_classes[&k].join(","));
    }
}

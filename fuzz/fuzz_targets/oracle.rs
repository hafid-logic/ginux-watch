//! Shared differential oracle (v2.7-2): ginux-oci `Rootfs` (kernel semantics,
//! kernel-faithful 256-byte path view) versus the reference `tar` crate on the
//! SAME input bytes. Used by `diff_matrix` (deterministic crafted cases) and
//! `diff_pax_tar` (libFuzzer record-only target).
//!
//! Upstream is consumed READ-ONLY via the path dependency; nothing is modified.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::io::{Cursor, Write};
use std::os::unix::ffi::OsStrExt;

pub const TAR_BLOCK: usize = 512;
/// Same buffer the kernel uses for entry paths (TAR_PREFIX_SIZE+1+TAR_NAME_SIZE).
pub const PATH_BUF: usize = 256;

// ---------------------------------------------------------------- construction

pub fn oct_field(value: u64, width: usize) -> Vec<u8> {
    // width-1 octal digits + NUL terminator (standard ustar layout).
    let digits = format!("{:0width$o}", value, width = width - 1);
    let mut out = digits.into_bytes();
    out.push(0);
    out
}

/// One PAX record: "<len> key=value\n" with len = total record length.
pub fn pax_record(key: &str, value: &[u8]) -> Vec<u8> {
    let mut digits = 1usize;
    loop {
        let total = digits + 1 + key.len() + 1 + value.len() + 1;
        if format!("{}", total).len() == digits {
            let mut r = format!("{} ", total).into_bytes();
            r.extend_from_slice(key.as_bytes());
            r.push(b'=');
            r.extend_from_slice(value);
            r.push(b'\n');
            return r;
        }
        digits += 1;
    }
}

/// Build a 512-byte ustar header (+ padded data) for one entry.
/// `size_field`/`mtime_field` override the raw field bytes (base-256, spaces,
/// junk) for strictness probes; `link`/`prefix` may be empty.
pub fn ustar_entry(
    name: &[u8],
    typeflag: u8,
    size: u64,
    mode: u64,
    link: &[u8],
    prefix: &[u8],
    data: &[u8],
    size_field: Option<&[u8]>,
    mtime_field: Option<&[u8]>,
) -> Vec<u8> {
    let mut h = vec![0u8; TAR_BLOCK];
    h[..name.len()].copy_from_slice(name);
    h[100..108].copy_from_slice(&oct_field(mode, 8));
    h[108..116].copy_from_slice(&oct_field(0, 8)); // uid
    h[116..124].copy_from_slice(&oct_field(0, 8)); // gid
    match size_field {
        Some(raw) => h[124..124 + raw.len()].copy_from_slice(raw),
        None => h[124..136].copy_from_slice(&oct_field(size, 12)),
    }
    match mtime_field {
        Some(raw) => h[136..136 + raw.len()].copy_from_slice(raw),
        None => h[136..148].copy_from_slice(&oct_field(0, 12)),
    }
    h[156] = typeflag;
    h[157..157 + link.len()].copy_from_slice(link);
    h[257..263].copy_from_slice(b"ustar\0");
    h[263..265].copy_from_slice(b"00");
    h[345..345 + prefix.len()].copy_from_slice(prefix);
    // checksum: spaces over 148..156, unsigned sum, 6 digits + NUL + space.
    let sum: u64 = h
        .iter()
        .enumerate()
        .map(|(i, b)| if (148..156).contains(&i) { 0x20 } else { *b as u64 })
        .sum();
    let mut chk = format!("{:06o}", sum).into_bytes();
    chk.push(0);
    chk.push(b' ');
    h[148..156].copy_from_slice(&chk);
    let mut out = h;
    out.extend_from_slice(data);
    let padded = data.len().div_ceil(TAR_BLOCK) * TAR_BLOCK;
    out.resize(TAR_BLOCK + padded, 0);
    out
}

/// PAX extended header ('x') carrying the given payload (already records).
pub fn x_header(payload: &[u8]) -> Vec<u8> {
    ustar_entry(b"PaxHeaders/x", b'x', payload.len() as u64, 0o644, b"", b"", payload, None, None)
}

/// Recompute and store the unsigned checksum of a patched 512-byte header.
pub fn set_checksum(header: &mut [u8]) {
    let sum: u64 = header[..TAR_BLOCK]
        .iter()
        .enumerate()
        .map(|(i, b)| if (148..156).contains(&i) { 0x20 } else { *b as u64 })
        .sum();
    let mut chk = format!("{:06o}", sum).into_bytes();
    chk.push(0);
    chk.push(b' ');
    header[148..156].copy_from_slice(&chk);
}

/// Global PAX header ('g').
pub fn g_header(payload: &[u8]) -> Vec<u8> {
    ustar_entry(b"PaxHeaders/g", b'g', payload.len() as u64, 0o644, b"", b"", payload, None, None)
}

pub fn terminator() -> Vec<u8> {
    vec![0u8; TAR_BLOCK * 2]
}

pub fn assemble(parts: &[Vec<u8>]) -> Vec<u8> {
    let mut out = Vec::new();
    for p in parts {
        out.extend_from_slice(p);
    }
    out
}

// ---------------------------------------------------------------- ginux view

#[derive(Clone, Debug)]
pub struct GEntry {
    /// Kernel-visible path via copy_path into the kernel 256-byte buffer
    /// (None = path does not fit / entry invisible through that API).
    pub path: Option<Vec<u8>>,
    pub kind: &'static str,
    pub data_len: usize,
    pub link: Vec<u8>,
    pub mode: u32,
}

/// Parse with ginux-oci and extract the kernel-faithful semantic view.
/// Err = Rootfs::parse returned None (whole archive rejected).
pub fn ginux_view(bytes: &[u8]) -> Result<Vec<GEntry>, &'static str> {
    let rootfs = ginux_oci::Rootfs::parse(bytes).ok_or("None")?;
    let mut out = Vec::new();
    let mut offset = 0usize;
    loop {
        let Some((entry, next)) = rootfs.entry_and_next_at_offset(offset) else {
            break;
        };
        let index = out.len();
        let mut buf = [0u8; PATH_BUF];
        let path = rootfs.copy_path(index, &mut buf).map(|l| buf[..l].to_vec());
        out.push(GEntry {
            path,
            kind: match entry.kind {
                ginux_oci::EntryKind::File => "file",
                ginux_oci::EntryKind::Directory => "dir",
                ginux_oci::EntryKind::Symlink => "symlink",
                ginux_oci::EntryKind::Hardlink => "hardlink",
            },
            data_len: entry.data.len(),
            link: entry.link.to_vec(),
            mode: entry.mode,
        });
        if next <= offset {
            break;
        }
        offset = next;
    }
    Ok(out)
}

// ---------------------------------------------------------------- tar view

#[derive(Clone, Debug)]
pub struct TEntry {
    pub name: Vec<u8>,
    pub kind: String,
    pub size_entry: u64,
    pub size_hdr: u64,
    pub link: Option<Vec<u8>>,
    pub mode: u32,
}

/// Parse with the reference `tar` crate. Err = the crate rejected/errored.
pub fn tar_view(bytes: &[u8]) -> Result<Vec<TEntry>, String> {
    let mut archive = tar::Archive::new(Cursor::new(bytes.to_vec()));
    let entries = archive.entries().map_err(|e| format!("entries: {}", e))?;
    let mut out = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| format!("entry@{}: {}", out.len(), e))?;
        let name = entry
            .path()
            .map(|p| p.as_os_str().as_bytes().to_vec())
            .map_err(|e| format!("path: {}", e))?;
        let kind = format!("{:?}", entry.header().entry_type());
        let size_hdr = entry.header().size().map_err(|e| format!("size: {}", e))?;
        let size_entry: u64 = entry.size();
        let link = entry
            .link_name()
            .ok()
            .flatten()
            .map(|s| s.as_os_str().as_bytes().to_vec());
        let mode = entry.header().mode().unwrap_or(0) & 0o7777;
        out.push(TEntry { name, kind, size_entry, size_hdr, link, mode });
    }
    Ok(out)
}

// ---------------------------------------------------------------- comparison

#[derive(Clone, Debug)]
pub struct Diff {
    /// Stable descriptor key (class + index when applicable).
    pub key: String,
    pub detail: String,
}

fn tar_kind(kind: &str) -> String {
    match kind {
        "Regular" => "file",
        "Directory" => "dir",
        "Symlink" => "symlink",
        "Link" => "hardlink", // tar::EntryType::Link = typeflag '1'
        other => return format!("other({})", other),
    }
    .to_string()
}

/// Compare the two semantic views. Normalizations: directory trailing '/'
/// (tar keeps it, ginux strips), mode masked to 0o7777 on both sides.
pub fn compare(g: &Result<Vec<GEntry>, &'static str>, t: &Result<Vec<TEntry>, String>) -> Vec<Diff> {
    let mut diffs = Vec::new();
    match (g, t) {
        (Err(w), Ok(_)) => diffs.push(Diff {
            key: "PARSE".into(),
            detail: format!("ginux=reject({}) tar=accept", w),
        }),
        (Ok(_), Err(e)) => diffs.push(Diff {
            key: "PARSE".into(),
            detail: format!("ginux=accept tar=reject({})", truncate(e, 80)),
        }),
        (Err(_), Err(_)) => {}
        (Ok(gv), Ok(tv)) => {
            if gv.len() != tv.len() {
                diffs.push(Diff {
                    key: "COUNT".into(),
                    detail: format!("ginux={} tar={}", gv.len(), tv.len()),
                });
            }
            for i in 0..gv.len().min(tv.len()) {
                let g = &gv[i];
                let t = &tv[i];
                // PATH
                let mut tname = t.name.clone();
                if t.kind == "Directory" && tname.ends_with(b"/") {
                    tname.pop();
                }
                let gpath = g.path.clone().unwrap_or_else(|| b"<invisible>".to_vec());
                if gpath != tname {
                    diffs.push(Diff {
                        key: format!("PATH@{}", i),
                        detail: format!("ginux={:?} tar={:?}", gpath, tname),
                    });
                }
                // KIND
                let tkind = tar_kind(&t.kind);
                if g.kind != tkind {
                    diffs.push(Diff {
                        key: format!("KIND@{}", i),
                        detail: format!("ginux={} tar={}", g.kind, tkind),
                    });
                }
                // SIZE (files carry data; ginux data_len vs tar effective size)
                if g.data_len as u64 != t.size_entry {
                    diffs.push(Diff {
                        key: format!("SIZE@{}", i),
                        detail: format!(
                            "ginux={} tar={} (hdr={})",
                            g.data_len, t.size_entry, t.size_hdr
                        ),
                    });
                }
                // LINK
                let tlink = t.link.clone().unwrap_or_default();
                if g.link != tlink {
                    diffs.push(Diff {
                        key: format!("LINK@{}", i),
                        detail: format!("ginux={:?} tar={:?}", g.link, tlink),
                    });
                }
                // MODE (raw kept by ginux; tar masks to 0o7777)
                if g.mode & 0o7777 != t.mode {
                    diffs.push(Diff {
                        key: format!("MODE@{}", i),
                        detail: format!("ginux={:o} tar={:o}", g.mode, t.mode),
                    });
                }
            }
        }
    }
    diffs
}

pub fn truncate(s: &str, n: usize) -> String {
    if s.len() <= n {
        s.to_string()
    } else {
        let mut end = n;
        while end > 0 && !s.is_char_boundary(end) {
            end -= 1;
        }
        format!("{}…", &s[..end])
    }
}

pub fn hash_key(diff: &Diff, input_len: usize) -> String {
    let mut h = DefaultHasher::new();
    diff.key.hash(&mut h);
    diff.detail.hash(&mut h);
    format!("{:016x}-{}", h.finish(), input_len)
}

/// Record-only dump: one file per unique (descriptor,input) so the same
/// semantic difference is never recorded twice (dedup gate at capture time).
pub fn dump_unique(dir: &str, diff: &Diff, input: &[u8]) {
    let key = hash_key(diff, input.len());
    let _ = std::fs::create_dir_all(dir);
    let input_path = format!("{}/{}.input", dir, key);
    if std::fs::File::options().create_new(true).write(true).open(&input_path).is_ok() {
        if let Ok(mut f) = std::fs::File::create(format!("{}/{}.desc", dir, key)) {
            let _ = writeln!(f, "class={}", diff.key);
            let _ = writeln!(f, "detail={}", diff.detail);
            let _ = writeln!(f, "input_len={}", input.len());
        }
        eprintln!("DIFF {} {} :: {}", key, diff.key, diff.detail);
        let _ = std::fs::write(&input_path, input);
    }
}

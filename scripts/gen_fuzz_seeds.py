#!/usr/bin/env python3
"""v2.6 seed corpus generator for the oci_surfaces fuzz target.

Seeds = valid tar/PAX archives mirroring upstream crates/oci tests at pin
82df3d71 + crafted boundary cases (size 0, 2^32 and max-octal thresholds,
aligned/padded sizes, prefix+name splits, whiteouts, PAX chains) + registry
JSON/bearer/reference surfaces. Output: fuzz/corpus-seed/ (committed).

Includes a mini tar-walker self-test that simulates upstream Rootfs::parse
well-formedness (ustar magic + checksum + padding) so a generator bug cannot
silently produce dead seeds.
"""
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "ginux-watch", "fuzz", "corpus-seed")


def tar_header(path=b"", data=b"", kind=b"0", link=b"", mode=b"0000755\0",
               prefix=b"", size_field=None, magic=b"ustar\x0000", corrupt=0):
    h = bytearray(512)
    h[0:len(path)] = path
    h[100:108] = mode
    h[108:116] = b"0000000\0"
    h[116:124] = b"0000000\0"
    sz = size_field if size_field is not None else b"%011o\0" % len(data)
    assert len(sz) == 12, "size field must be 12 bytes"
    h[124:136] = sz
    h[136:148] = b"00000000000\0"
    h[148:156] = b"        "
    h[156] = kind if isinstance(kind, int) else ord(kind)
    h[157:157 + len(link)] = link
    h[257:265] = magic[:8].ljust(8, b"\0")
    h[345:345 + len(prefix)] = prefix
    total = sum(h) + corrupt
    h[148:156] = b"%06o\0 " % total
    return bytes(h)


def entry(path=b"", data=b"", kind=b"0", link=b"", prefix=b"", **kw):
    d = tar_header(path=path, data=data, kind=kind, link=link, prefix=prefix, **kw)
    d += data
    d += b"\0" * ((-len(data)) % 512)
    return d


def pax_record(key: bytes, value: bytes) -> bytes:
    body = key + b"=" + value
    n = len(body) + 2
    while len(str(n)) + len(body) + 2 != n:
        n = len(str(n)) + len(body) + 2
    return str(n).encode() + b" " + body + b"\n"


def pax_entry(records: bytes):
    return entry(b"PaxHeaders/0", records, kind=b"x")


def archive(*entries, terminator=True, trailing=b"", truncate=None):
    out = b"".join(entries)
    if terminator:
        out += b"\0" * 1024
    out += trailing
    if truncate is not None:
        out = out[:truncate]
    return out


def simulate(entries):
    """Mini walker mirroring upstream Rootfs::parse structure checks."""
    off, count = 0, 0
    while True:
        blk = entries[off:off + 512]
        if len(blk) < 512:
            return None  # truncated
        if blk == b"\0" * 512:
            second = entries[off + 512:off + 1024]
            if second != b"\0" * 512 or any(entries[off + 1024:]):
                return None
            return count
        if blk[257:263] != b"ustar\0":
            return None
        stored = int.from_bytes(b"", "big") if False else None
        try:
            stored = int(blk[148:156].replace(b"\0", b" ").strip() or b"0", 8)
        except ValueError:
            return None
        calc = sum(blk[0:148]) + 8 * 0x20 + sum(blk[156:512])
        if stored != calc:
            return None
        size = int(blk[124:135].replace(b"\0", b" ").strip() or b"0", 8)
        off += 512 + (size + 511) // 512 * 512
        count += 1


def main():
    os.makedirs(OUT, exist_ok=True)
    seeds = {}

    # ---- tar/PAX: valid shapes from upstream tests (82df3d71) ----
    seeds["t01_file"] = archive(entry(b"bin/busybox", b"ELF"))
    seeds["t02_symlink"] = archive(entry(b"bin/sh", kind=b"2", link=b"/bin/busybox"))
    seeds["t03_hardlink"] = archive(entry(b"bin/tool", kind=b"1", link=b"bin/busybox"))
    seeds["t04_dir"] = archive(entry(b"etc/", kind=b"5"), entry(b"etc/value", b"new"))
    seeds["t05_pax_path"] = archive(
        pax_entry(pax_record(b"path", b"very/deeply/nested/long-path-name")),
        entry(b"placeholder", b"x"))
    # iterative PAX chains (4294c0a7): two chained x headers, merge semantics
    seeds["t06_pax_chain"] = archive(
        pax_entry(pax_record(b"path", b"chain/first")),
        pax_entry(pax_record(b"linkpath", b"chain/target")),
        entry(b"ph", kind=b"2", link=b"orig"))
    # duplicate path key -> None branch
    seeds["t07_pax_dup"] = archive(
        pax_entry(pax_record(b"path", b"a/b") + pax_record(b"path", b"c/d")),
        entry(b"ph", b"x"))
    # PAX path for directory with trailing slash -> strip_suffix branch
    seeds["t08_pax_dir_slash"] = archive(
        pax_entry(pax_record(b"path", b"etc/long-dir-name/")),
        entry(b"ph", kind=b"5"))
    # prefix+name split; name exactly 100 bytes (no NUL terminator branch)
    long_name = b"n" * 100
    seeds["t09_prefix_split"] = archive(
        entry(long_name, b"x", prefix=b"pre/fix"))
    seeds["t09b_prefix_path"] = archive(
        entry(b"tail", b"x", prefix=b"head/shoulders"))
    # size boundaries: 0, exactly 512, 513 (padding), 2^32, max 11-digit octal
    seeds["t10_size0"] = archive(entry(b"empty", b""))
    seeds["t11_size512"] = archive(entry(b"blk", b"B" * 512))
    seeds["t12_size513"] = archive(entry(b"blk", b"B" * 513))
    seeds["t13_size_2p32"] = archive(entry(b"big", b"", size_field=b"40000000000\0"))
    seeds["t14_size_max"] = archive(entry(b"max", b"", size_field=b"77777777777\0"))
    # whiteouts + opaque dir (whiteout_hides branches)
    seeds["t15_whiteout"] = archive(entry(b"etc/value", b"old"),
                                    entry(b"etc/.wh.value", b""))
    seeds["t16_opaque"] = archive(entry(b"etc/", kind=b"5"),
                                  entry(b"etc/.wh..wh..opq", b""))
    seeds["t17_replacement"] = archive(entry(b"etc/value", b"old"),
                                       entry(b"etc/value", b"new"))
    # rejection shapes (error branches)
    seeds["t18_traverse"] = archive(entry(b"../escape", b"x"))
    seeds["t19_gnu_magic"] = archive(entry(b"g", b"x", magic=b"ustar  \0\0"))
    seeds["t20_corrupt"] = archive(entry(b"c", b"x", corrupt=1))
    seeds["t21_trailing"] = archive(entry(b"a", b"x"), trailing=b"\x01")
    seeds["t22_truncated"] = archive(entry(b"bin/sh", b"x"), truncate=600)
    seeds["t23_empty"] = b"\0" * 1024
    seeds["t24_zero_nonzero"] = b"\0" * 512 + b"\x01" * 512 + b"\0" * 512
    seeds["t25_after_terminator"] = b"\0" * 1024 + b"\x01" * 512
    seeds["t26_kind_L"] = archive(entry(b"gnu-long", b"x", kind=b"L"))
    seeds["t27_mode_spaces"] = archive(entry(b"m", b"x", mode=b"   755 \0"))
    seeds["t28_mode_blank"] = archive(entry(b"m", b"x", mode=b"        "))
    seeds["t29_dot_component"] = archive(entry(b"a/./b", b"x"))
    seeds["t30_multi"] = archive(entry(b"etc/", kind=b"5"),
                                 entry(b"etc/v", b"1"),
                                 entry(b"bin/sh", kind=b"2", link=b"/bin/busy"),
                                 entry(b"bin/tool", kind=b"1", link=b"bin/busy"),
                                 entry(b"etc/v", b"2"))

    # ---- registry JSON / bearer / digest surfaces ----
    d64 = "0123456789abcdef" * 4
    digest = "sha256:" + d64
    seeds["j01_index_match"] = (
        '{"schemaVersion":2,"mediaType":"application/vnd.oci.image.index.v1+json",'
        '"manifests":[{"mediaType":"application/vnd.oci.image.manifest.v1+json",'
        f'"digest":"{digest}","size":611,"platform":{{"architecture":"arm64","os":"linux"}}}},'
        '{"mediaType":"application/vnd.oci.image.manifest.v1+json",'
        f'"digest":"{digest}","size":612,"platform":{{"architecture":"amd64","os":"linux"}}}}]}}'
    ).encode()
    seeds["j02_manifest"] = (
        '{"schemaVersion":2,"config":{"mediaType":"application/vnd.oci.image.config.v1+json",'
        f'"digest":"{digest}","size":581}},"layers":[{{"mediaType":'
        '"application/vnd.oci.image.layer.v1.tar+gzip",'
        f'"digest":"{digest}","size":3651200}}]}}'
    ).encode()
    seeds["j03_manifest_16_layers"] = (
        '{"schemaVersion":2,"config":{"mediaType":"m","digest":"' + digest + '","size":1},'
        '"layers":[' + ",".join(
            '{"mediaType":"m","digest":"' + digest + '","size":1}' for _ in range(16)
        ) + ']}').encode()
    seeds["j04_config"] = (
        '{"architecture":"amd64","os":"linux","rootfs":{"type":"layers"}}').encode()
    seeds["j05_config_variant"] = (
        '{"architecture":"arm64","os":"linux","variant":"v8"}').encode()
    seeds["j06_challenge"] = (
        b'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",'
        b'scope="repository:library/alpine:pull"')
    seeds["j07_token"] = b'{"token":"signed-token"}'
    seeds["j08_access_token"] = b'{"access_token":"alternate-token"}\n'
    seeds["j09_short_digest"] = b'{"schemaVersion":2,"config":{"mediaType":"m",' \
                                b'"digest":"sha256:abcd","size":1},"layers":[{"mediaType":"m",' \
                                b'"digest":"' + digest.encode() + b'","size":1}]}'
    seeds["j10_index_windows"] = (
        '{"schemaVersion":2,"manifests":[{"mediaType":"manifest","digest":"' + digest +
        '","size":1,"platform":{"architecture":"amd64","os":"windows"}}]}').encode()

    # ---- image reference surfaces ----
    for i, r in enumerate([
        b"alpine", b"rockylinux/rockylinux:10",
        b"registry.example:5000/team/image:v1", ("alpine@" + digest).encode(),
        b"UPPER/image:tag", b"docker.io//image:tag", b"image:",
        ("image@sha256:" + "g" * 64).encode(), b"localhost:5000/x",
        b"a" * 129, b"x" * 128, b"repo.name_with.dots:8080/n/s:v1_2",
    ]):
        seeds[f"r{i:02d}_ref"] = r

    ok, dead = 0, []
    for name, blob in seeds.items():
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(blob)
        if name.startswith("t") and name[1].isdigit():
            # structural self-test only for pure-tar archives that should parse
            expect_parse = name in {"t01_file", "t02_symlink", "t03_hardlink",
                                    "t04_dir", "t05_pax_path", "t06_pax_chain",
                                    "t09b_prefix_path", "t10_size0",
                                    "t11_size512", "t12_size513",
                                    "t15_whiteout", "t16_opaque",
                                    "t17_replacement", "t27_mode_spaces",
                                    "t30_multi", "t09_prefix_split"}
            got = simulate(blob)
            if expect_parse:
                if got is None:
                    dead.append((name, "should parse"))
                else:
                    ok += 1
            elif got and name in {"t20_corrupt", "t21_trailing",
                                  "t22_truncated", "t23_empty",
                                  "t24_zero_nonzero",
                                  "t25_after_terminator"}:
                dead.append((name, "should be rejected"))
    print(f"seeds written: {len(seeds)}; structural-walk OK on {ok}")
    if dead:
        print("DEAD SEEDS:", dead)
        sys.exit(1)


if __name__ == "__main__":
    main()

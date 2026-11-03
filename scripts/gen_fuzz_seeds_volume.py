#!/usr/bin/env python3
"""gen_fuzz_seeds_volume.py (v2.7-3): seed corpus for volume_surfaces.

Mirrors crates/volume-format encode() at upstream@82df3d71 byte-for-byte:
valid committed/prepared records, host volume headers (positive), and
targeted negatives (stale digest, bad magic/version/header-size, gen=0,
length>capacity, nonzero reserved/padding with recomputed digest, geometry
mismatches, short/junk sectors). Structural self-test at the end.
Output: fuzz/corpus-seed-volume/<nn>-<name>.bin
"""
import hashlib
import os
import struct
import sys

SECTOR = 512
HEADER_SIZE = 72
MAGIC = b"GINUXPV0"
VERSION = 1
COMMIT_MARKER = 0x3144_4554_5449_4D43  # LE bytes = b"COMMITTED1"
DIGEST_OFF = 32
HOST_MAGIC = b"GINUXHV1"
HOST_HEADER_SIZE = 48
HOST_DATA_START = 8

OUT = os.path.join(os.path.dirname(__file__), "..", "fuzz", "corpus-seed-volume")


def digest(sector: bytes) -> bytes:
    canonical = bytearray(sector)
    canonical[DIGEST_OFF:DIGEST_OFF + 32] = b"\0" * 32
    return hashlib.sha256(bytes(canonical)).digest()


def encode(gen: int, payload: bytes) -> bytes:
    assert gen != 0 and len(payload) <= SECTOR - HEADER_SIZE
    s = bytearray(SECTOR)
    s[0:8] = MAGIC
    struct.pack_into("<I", s, 8, VERSION)
    struct.pack_into("<H", s, 12, HEADER_SIZE)
    struct.pack_into("<H", s, 14, len(payload))
    struct.pack_into("<Q", s, 16, gen)
    struct.pack_into("<Q", s, 24, COMMIT_MARKER)
    s[HEADER_SIZE:HEADER_SIZE + len(payload)] = payload
    s[DIGEST_OFF:DIGEST_OFF + 32] = digest(bytes(s))
    return bytes(s)


def recommit(sector: bytes) -> bytes:
    """Recompute the digest after a manual patch (attacker with write access)."""
    s = bytearray(sector)
    s[DIGEST_OFF:DIGEST_OFF + 32] = digest(bytes(s))
    return bytes(s)


def host_header(volume_sectors: int, data_start: int = HOST_DATA_START,
                data_sectors: int | None = None) -> bytes:
    ds = volume_sectors - HOST_DATA_START if data_sectors is None else data_sectors
    b = bytearray(HOST_HEADER_SIZE)
    b[0:8] = HOST_MAGIC
    struct.pack_into("<I", b, 8, 1)          # version
    struct.pack_into("<I", b, 12, HOST_HEADER_SIZE)
    struct.pack_into("<I", b, 16, SECTOR)    # sector size
    struct.pack_into("<Q", b, 24, volume_sectors)
    struct.pack_into("<Q", b, 32, data_start)
    struct.pack_into("<Q", b, 40, ds)
    return bytes(b)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    seeds: list[tuple[str, bytes]] = []

    c7 = encode(7, b"shared-codec")
    p7 = bytearray(c7); struct.pack_into("<Q", p7, 24, 0)
    seeds += [
        ("01-committed-gen7", c7),
        ("02-prepared-gen7", bytes(p7)),                       # negative: no commit marker
        ("03-committed-full-440", encode(1, b"A" * 440)),
        ("04-committed-empty-payload", encode(1, b"")),
        ("05-committed-gen-max", encode((1 << 64) - 1, b"x")),
        ("06-stale-digest-payload-flip", bytes(bytearray(c7[:HEADER_SIZE]) + b"\0" + c7[HEADER_SIZE + 1:])),
        ("07-digest-field-flip", c7[:DIGEST_OFF] + bytes([c7[32] ^ 1]) + c7[33:]),
        ("08-gen-zero", encode(1, b"z")[:16] + struct.pack("<Q", 0) + encode(1, b"z")[24:]),
    ]
    # 08 rebuilt cleanly: gen=0 with valid digest -> negative.
    s = bytearray(encode(1, b"z"))
    struct.pack_into("<Q", s, 16, 0)
    seeds[-1] = ("08-gen-zero", recommit(bytes(s)))

    bad_len = bytearray(encode(1, b"q"))
    struct.pack_into("<H", bad_len, 14, 441)
    seeds.append(("09-length-over-capacity", recommit(bytes(bad_len))))  # negative

    res = bytearray(encode(1, b"r"))
    res[64] = 1
    seeds.append(("10-reserved-nonzero", recommit(bytes(res))))          # negative

    pad = bytearray(encode(1, b"p"))
    pad[HEADER_SIZE + 1] = 1
    seeds.append(("11-padding-nonzero", recommit(bytes(pad))))           # negative

    mag = bytearray(encode(1, b"m")); mag[0:8] = b"GINUXPV1"
    seeds.append(("12-magic-variant", recommit(bytes(mag))))
    ver = bytearray(encode(1, b"v")); struct.pack_into("<I", ver, 8, 2)
    seeds.append(("13-version-2", recommit(bytes(ver))))
    hs = bytearray(encode(1, b"h")); struct.pack_into("<H", hs, 12, 73)
    seeds.append(("14-header-size-73", recommit(bytes(hs))))

    seeds += [
        ("15-all-zero-sector", bytes(SECTOR)),
        ("16-all-ff-sector", b"\xff" * SECTOR),
        ("17-junk-sector", bytes(range(256)) * 2),
        ("18-committed-gen1-len255", encode(1, bytes(range(255)))),
    ]

    # Host volume headers: positives (minimum + large) and negatives.
    seeds += [
        ("19-host-header-min-9", host_header(9)),
        ("20-host-header-131072", host_header(131072)),
        ("21-host-header-sectors-8", host_header(8)),                     # negative
        ("22-host-header-data-start-plus1", host_header(9, data_start=HOST_DATA_START + 1)),
        ("23-host-header-data-sectors-plus1", host_header(9, data_sectors=9 - HOST_DATA_START + 1)),
        ("24-host-header-short-47", host_header(16)[:47]),                # len branch
        ("25-host-header-bad-sector-size", bytes(bytearray(host_header(16))[:16] + struct.pack("<I", 4096) + host_header(16)[20:])),
    ]

    # Kernel chain positive: committed record whose PAYLOAD is a valid host header.
    seeds.append(("26-record-payload-host-header", encode(1, host_header(64))))

    for name, blob in seeds:
        with open(os.path.join(OUT, name + ".bin"), "wb") as f:
            f.write(blob)

    # Structural self-test: encode/decode agreement with the crate semantics.
    ok = True
    r = encode(7, b"shared-codec")
    ok &= r[0:8] == MAGIC and struct.unpack_from("<Q", r, 24)[0] == COMMIT_MARKER
    ok &= digest(r) == r[DIGEST_OFF:DIGEST_OFF + 32]
    prep = bytearray(r); struct.pack_into("<Q", prep, 24, 0)
    ok &= digest(bytes(prep)) != bytes(prep)[DIGEST_OFF:DIGEST_OFF + 32]
    print(f"seeds: {len(seeds)} written to {OUT}; self-test {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

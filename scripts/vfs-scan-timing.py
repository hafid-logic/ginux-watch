#!/usr/bin/env python3
"""v5.3-3c: vfs-index scan timing — baseline vs overflow-checks=true, same machine.
Deterministic tar set; warmup 1 each; 12 alternating AB/BA pairs (=12 runs each,
total 24); median + range. No 'negligible' claims without numbers."""
import hashlib, io, os, statistics, subprocess, sys, time

import sys
EV = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = sys.argv[2] if len(sys.argv) > 2 else "./ginux-vfs-index-base"
FLAG = sys.argv[3] if len(sys.argv) > 3 else "./ginux-vfs-index-flag"
TAR = f"{EV}/scan-set.tar"
IDX = f"{EV}/scan-set.idx"

# --- 1. deterministic tar set: 400 entries x 256KiB pseudo-random payload (~100MiB)
if not os.path.exists(TAR) or os.path.getsize(TAR) < 220_000_000:
    import tarfile
    h = hashlib.sha256(b"ginux-scan-timing-seed").digest()
    with tarfile.open(TAR, "w", format=tarfile.USTAR_FORMAT) as tf:
        def stream(n):
            seed = hashlib.sha256(b"ginux-scan-timing-seed").digest()
            buf = bytearray()
            while len(buf) < n:
                seed = hashlib.sha256(seed).digest()
                buf += seed
            return bytes(buf[:n])
        # verify_index (main.rs:382-404) requires the Rocky runtime paths present,
        # regular files, >=4 bytes, ELF magic at data offset. Directory entries are
        # required too: resolve() walks path components, so ancestors must exist.
        elf = b"\x7fELF" + bytes(251) + stream(64)
        for d in ("usr", "usr/bin", "usr/lib64", "data"):
            ti = tarfile.TarInfo(d)
            ti.type = tarfile.DIRTYPE; ti.mode = 0o755; ti.mtime = 1700000000
            tf.addfile(ti)
        for req in ("usr/bin/bash", "usr/lib64/ld-linux-x86-64.so.2", "usr/lib64/libc.so.6"):
            ti = tarfile.TarInfo(req)
            ti.size = len(elf); ti.mode = 0o755; ti.mtime = 1700000000
            tf.addfile(ti, io.BytesIO(elf))
        for i in range(50_000):
            data = stream(4 * 1024)
            ti = tarfile.TarInfo(f"data/file_{i:03d}.bin")
            ti.size = len(data)
            ti.mode = 0o644
            ti.mtime = 1700000000
            tf.addfile(ti, io.BytesIO(data))
print(f"tar set: {os.path.getsize(TAR)} bytes ({os.path.getsize(TAR)/1024/1024:.1f} MiB)")

def one_run(binary):
    if os.path.exists(IDX):
        os.unlink(IDX)
    t0 = time.perf_counter()
    r = subprocess.run([binary, TAR, IDX], capture_output=True)
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        sys.exit(f"FAIL {binary}: rc={r.returncode} {r.stderr[:300]}")
    return dt

for b in (BASE, FLAG):          # warmup + sanity
    one_run(b)

samples = {"base": [], "flag": []}
order_log = []
for i in range(12):             # alternating AB/BA (order swap)
    if i % 2 == 0:
        order_log.append("base,flag")
        samples["base"].append(one_run(BASE))
        samples["flag"].append(one_run(FLAG))
    else:
        order_log.append("flag,base")
        samples["flag"].append(one_run(FLAG))
        samples["base"].append(one_run(BASE))

for k in ("base", "flag"):
    v = sorted(samples[k])
    med = statistics.median(v)
    print(f"{k:5s}: n={len(v)} median={med*1000:.1f}ms range=[{v[0]*1000:.1f}..{v[-1]*1000:.1f}]ms mean={statistics.mean(v)*1000:.1f}ms")
delta_med = (statistics.median(samples["flag"]) - statistics.median(samples["base"])) * 1000
print(f"median delta (flag-base): {delta_med:+.1f}ms")
print("orders:", " | ".join(order_log))
print("first idx sha256:", hashlib.sha256(open(IDX,'rb').read()).hexdigest()[:16])

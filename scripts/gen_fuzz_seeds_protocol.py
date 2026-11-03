#!/usr/bin/env python3
"""v2.6-4 seed corpus for the protocol_surfaces fuzz target.

Valid frames cribbed from upstream crates/protocol-state tests at pin
82df3d71 (FRAME, IPV4_FRAME with LOCAL/PEER constants) + crafted rejection
and boundary frames, with real internet-checksum computation.
Output: fuzz/corpus-seed-protocol/ (committed).
"""
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "ginux-watch", "fuzz", "corpus-seed-protocol")

LOCAL_MAC = bytes([0x52, 0x54, 0x00, 0x12, 0x34, 0x56])
PEER_MAC = bytes([0x52, 0x55, 0x0a, 0x00, 0x02, 0x02])
LOCAL_IP = bytes([10, 0, 2, 15])
PEER_IP = bytes([10, 0, 2, 2])


def cksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\0"
    s = sum((data[i] << 8) | data[i + 1] for i in range(0, len(data), 2))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF


def arp_frame(sender_mac=PEER_MAC, sender_ip=PEER_IP, target_mac=LOCAL_MAC,
              target_ip=LOCAL_IP, dst=LOCAL_MAC, hw_type=b"\x00\x01\x08\x00\x06\x04\x00\x02"):
    f = bytearray(42)
    f[0:6] = dst
    f[6:12] = sender_mac
    f[12:14] = b"\x08\x06"
    f[14:22] = hw_type
    f[22:28] = sender_mac
    f[28:32] = sender_ip
    f[32:38] = target_mac
    f[38:42] = target_ip
    return bytes(f)


def icmp_message(ident=0xBEEF, seq=1, payload=b"", mtype=8, code=0, bad_cksum=False):
    hdr = bytearray([mtype, code, 0, 0])
    hdr[4:6] = ident.to_bytes(2, "big")
    hdr[6:8] = seq.to_bytes(2, "big")
    hdr += payload
    c = cksum(bytes(hdr))
    if bad_cksum:
        c ^= 1
    hdr[2:4] = c.to_bytes(2, "big")
    return bytes(hdr)


def ipv4_frame(payload: bytes, src=PEER_IP, dst=LOCAL_IP, ttl=0x40,
               total_length=None, ident=0x1234, flags_frag=0x4000, proto=1,
               bad_cksum=False, ver_ihl=0x45):
    tl = (20 + len(payload)) if total_length is None else total_length
    hdr = bytearray(20)
    hdr[0] = ver_ihl
    hdr[1] = 0
    hdr[2:4] = tl.to_bytes(2, "big")
    hdr[4:6] = ident.to_bytes(2, "big")
    hdr[6:8] = flags_frag.to_bytes(2, "big")
    hdr[8] = ttl
    hdr[9] = proto
    hdr[12:16] = src
    hdr[16:20] = dst
    c = cksum(bytes(hdr))
    if bad_cksum:
        c ^= 1
    hdr[10:12] = c.to_bytes(2, "big")
    return bytes(hdr) + payload


def eth_ipv4(payload: bytes, dst=LOCAL_MAC, src=PEER_MAC, **kw):
    return dst + src + b"\x08\x00" + ipv4_frame(payload, **kw)


def main():
    os.makedirs(OUT, exist_ok=True)
    seeds = {}

    # ---- ARP (exact 42-byte frames) ----
    seeds["p01_arp_valid"] = arp_frame()
    seeds["p02_arp_mcast_sender"] = arp_frame(sender_mac=bytes([0x03]) + PEER_MAC[1:])
    seeds["p03_arp_zero_sender"] = arp_frame(sender_mac=b"\x00" * 6)
    seeds["p04_arp_bcast_sender"] = arp_frame(sender_mac=b"\xff" * 6)
    seeds["p05_arp_wrong_target_mac"] = arp_frame(target_mac=PEER_MAC)
    seeds["p06_arp_wrong_sender_ip"] = arp_frame(sender_ip=bytes([10, 0, 2, 3]))
    seeds["p07_arp_wrong_hwtype"] = arp_frame(hw_type=b"\x00\x01\x08\x00\x06\x04\x00\x01")
    seeds["p08_arp_wrong_dst"] = arp_frame(dst=PEER_MAC)
    seeds["p09_arp_len41"] = arp_frame()[:-1]
    seeds["p10_arp_len43"] = arp_frame() + b"\x00"

    # ---- IPv4 + ICMP (ethernet frames) ----
    echo = icmp_message()
    seeds["p11_ipv4_valid"] = eth_ipv4(echo)
    seeds["p12_ipv4_bad_cksum"] = eth_ipv4(echo, bad_cksum=True)
    seeds["p13_ipv4_fragment_mf"] = eth_ipv4(echo, flags_frag=0x2000)
    seeds["p14_ipv4_fragment_off"] = eth_ipv4(echo, flags_frag=0x0008)
    seeds["p15_ipv4_ttl0"] = eth_ipv4(echo, ttl=0)
    seeds["p16_ipv4_proto6"] = eth_ipv4(echo, proto=6)
    seeds["p17_len_lt20"] = eth_ipv4(echo, total_length=10)
    seeds["p17b_len_mismatch"] = eth_ipv4(echo, total_length=19 + len(echo))
    seeds["p18_ipv4_src_swap"] = eth_ipv4(echo, src=LOCAL_IP)
    seeds["p19_ipv4_dst_swap"] = eth_ipv4(echo, dst=PEER_IP)
    seeds["p20_ipv4_ver4"] = eth_ipv4(echo, ver_ihl=0x44)
    seeds["p21_ipv4_payload64"] = eth_ipv4(icmp_message(payload=bytes(range(64))))
    seeds["p22_ipv4_maxish"] = eth_ipv4(icmp_message(payload=b"\xab" * 1400))
    seeds["p23_ipv4_hdr_only"] = eth_ipv4(b"")  # payload empty: icmp Length err
    seeds["p24_ident_edge"] = eth_ipv4(echo, ident=0xFFFF)
    seeds["p25_short33"] = (eth_ipv4(echo))[:33]

    # ---- direct ICMP messages ----
    seeds["p26_icmp_valid"] = icmp_message()
    seeds["p27_icmp_type3"] = icmp_message(mtype=3)
    seeds["p28_icmp_code1"] = icmp_message(code=1)
    seeds["p29_icmp_bad_cksum"] = icmp_message(bad_cksum=True)
    seeds["p30_icmp_short7"] = b"\x08\x00\x00\x00\xbe\xef\x01"
    seeds["p31_icmp_payload512"] = icmp_message(payload=b"\x5a" * 512)
    seeds["p32_icmp_id_seq_edges"] = icmp_message(ident=0, seq=0xFFFF)
    seeds["p33_icmp_reply_type0"] = icmp_message(mtype=0)

    for name, blob in seeds.items():
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(blob)
    print(f"seeds written: {len(seeds)}")


if __name__ == "__main__":
    main()

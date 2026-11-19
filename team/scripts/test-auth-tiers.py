#!/usr/bin/env python3
"""test-auth-tiers.py — offline tests for v8.5 tier selection + device-flow parsing."""
import importlib.util, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
def lm(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
az = lm("az", REPO / "scripts/authz_check.py")
dev = lm("dev", REPO / "scripts/auth_device.py")
PASS, FAIL = 0, 0
def ok(n):
    global PASS; PASS += 1; print("ok  " + n)
def no(n, m=""):
    global FAIL; FAIL += 1; print("FAIL %s %s" % (n, m))
full = {"exec_env": True, "device_reachable": True, "app_ready": True, "owner_can_activate": True, "upload": True, "token_issuable": True}
ok("T1 tier0 when all available") if az.select_tier(full)[0] == "device_flow" else no("T1")
ok("T2 no exec-env + upload => A") if az.select_tier(dict(full, exec_env=False))[0] == "upload_file" else no("T2")
ok("T3 no exec-env no upload => B") if az.select_tier(dict(full, exec_env=False, upload=False))[0] == "short_lived_pat" else no("T3")
ok("T4 no token channel => C") if az.select_tier(dict(full, exec_env=False, upload=False, token_issuable=False))[0] == "zero_token" else no("T4")
ok("T5 high sensitivity => C") if az.select_tier(dict(full, high_sensitivity=True))[0] == "zero_token" else no("T5")
ok("T6 device unreachable + upload => A") if az.select_tier(dict(full, device_reachable=False))[0] == "upload_file" else no("T6")
ok("T7 owner cannot activate + no upload => B") if az.select_tier(dict(full, owner_can_activate=False, upload=False))[0] == "short_lived_pat" else no("T7")
uc, uri, exp, iv = dev.parse_code_response({"user_code": "ABCD-1234", "verification_uri": "https://github.com/login/device", "device_code": "SECRET", "expires_in": 900, "interval": 5})
ok("T8 parse code response") if (uc == "ABCD-1234" and exp == 900 and iv == 5) else no("T8")
s, t, e = dev.parse_token_response({"access_token": "ghu_x", "expires_in": 28800})
ok("T9 parse token ok") if (s == "ok" and e == 28800) else no("T9")
s2, t2, e2 = dev.parse_token_response({"error": "authorization_pending"})
ok("T10 parse pending") if (s2 == "authorization_pending" and t2 is None) else no("T10")
print("auth-tiers tests: %d/%d pass" % (PASS, PASS + FAIL))
sys.exit(1 if FAIL else 0)

#!/usr/bin/env python3
"""auth_device.py — v8.5 tier-0: GitHub App device flow (owner-approved plan).

--start: request device code; print ONLY user_code + verification_uri; store
device_code in work/device-flow.json (600). --poll: exchange stored device_code
for token; store token in work/keys/gh-token (600). --cleanup: shred token.
NEVER prints device_code or token. Pure parse helpers are offline-tested.
"""
import argparse, json, os, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CLIENT_ID = "Iv23likXwrakJW83j8q7"  # public identifier, not a secret
CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
KEY = ROOT / "work/keys/gh-token"
DF = ROOT / "work/device-flow.json"
GRANT = "urn:ietf:params:oauth:grant-type:device_code"

def post(url, fields):
    data = "&".join("%s=%s" % (k, v) for k, v in fields.items()).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "ginux-watch",
        "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def parse_code_response(d):
    return d["user_code"], d["verification_uri"], int(d.get("expires_in", 900)), int(d.get("interval", 5))

def parse_token_response(d):
    if "access_token" in d:
        return ("ok", d["access_token"], int(d.get("expires_in", 0)))
    return (d.get("error", "unknown"), None, 0)

def store_token(tok):
    KEY.parent.mkdir(parents=True, exist_ok=True)
    KEY.write_text(tok + "\n"); os.chmod(KEY, 0o600)

def cleanup():
    if KEY.exists():
        n = KEY.stat().st_size
        KEY.write_bytes(os.urandom(n)); KEY.unlink()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", action="store_true")
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--cleanup", action="store_true")
    a = ap.parse_args()
    if a.cleanup:
        cleanup(); print("token shredded"); return 0
    if a.start:
        d = post(CODE_URL, {"client_id": CLIENT_ID})
        uc, uri, exp, iv = parse_code_response(d)
        DF.parent.mkdir(parents=True, exist_ok=True)
        DF.write_text(json.dumps({"device_code": d["device_code"], "interval": iv, "expires": time.time() + exp}))
        os.chmod(DF, 0o600)
        print("Activate at %s  code: %s  (expires %ss)" % (uri, uc, exp))
        print("device_code stored locally (never printed). Run --poll after activation.")
        return 0
    if a.poll:
        dc = json.loads(DF.read_text())["device_code"]
        d = post(TOKEN_URL, {"client_id": CLIENT_ID, "device_code": dc, "grant_type": GRANT})
        status, tok, exp = parse_token_response(d)
        if status == "ok":
            store_token(tok); print("token stored 600 (expires_in=%ss); never printed." % exp); return 0
        print("status: %s" % status)
        return 1 if status in ("expired_token", "device_flow_disabled", "incorrect_client_credentials", "unsupported_grant_type") else 2
    ap.print_help(); return 2

if __name__ == "__main__":
    raise SystemExit(main())

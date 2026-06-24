"""Test different token encoding strategies for pagination."""
from curl_cffi import requests
import hmac, hashlib, time, json
import urllib.parse

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token_v1(path):
    """Original: raw path in acl."""
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def token_v2(path):
    """URL-encode the path in acl."""
    encoded = urllib.parse.quote(path, safe="/")
    t = f"exp={int(time.time())+60}~acl={encoded}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def token_v3(path):
    """Use only the path portion (before ?) in acl."""
    path_only = path.split("?")[0]
    t = f"exp={int(time.time())+60}~acl={path_only}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def token_v4(path):
    """Encode & as %26 in acl."""
    encoded = path.replace("&", "%26")
    t = f"exp={int(time.time())+60}~acl={encoded}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

s = requests.Session(impersonate="chrome")

# Test with the paginated URL
path = "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=12"

for name, tok_fn in [("v1-raw", token_v1), ("v2-quote", token_v2), ("v3-path-only", token_v3), ("v4-encode-amp", token_v4)]:
    tok = tok_fn(path)
    r = s.get(
        f"https://hs-consumer-api.cricinfo.com{path}",
        headers={
            "x-hsci-auth-token": tok,
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
        }
    )
    content = r.json().get("content", {}) if r.status_code == 200 else {}
    comments = content.get("comments", [])
    print(f"{name}: status={r.status_code}, comments={len(comments)}")
    if r.status_code == 400:
        print(f"  Error: {r.text[:200]}")

# Also test: maybe the escapeEarly flag means we encode % in the token differently
print("\n--- Also test base path without pagination (sanity check) ---")
base_path = "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC"
for name, tok_fn in [("v1-raw", token_v1), ("v3-path-only", token_v3)]:
    tok = tok_fn(base_path)
    r = s.get(
        f"https://hs-consumer-api.cricinfo.com{base_path}",
        headers={
            "x-hsci-auth-token": tok,
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
        }
    )
    content = r.json().get("content", {}) if r.status_code == 200 else {}
    comments = content.get("comments", [])
    print(f"{name}: status={r.status_code}, comments={len(comments)}")

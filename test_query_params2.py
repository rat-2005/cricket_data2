"""Test exact query params to find what causes 400 errors."""
from curl_cffi import requests
import hmac, hashlib, time

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def api_get(params):
    path = f"/v1/pages/match/commentary?{params}"
    tok = token(path)
    r = requests.get(
        f"https://hs-consumer-api.cricinfo.com{path}",
        headers={
            "x-hsci-auth-token": tok,
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
            "Accept": "application/json",
        },
        impersonate="chrome"
    )
    return r.status_code, r.text

base = "lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC"

tests = [
    f"{base}&fromInningOver=12",
    f"{base}&fromInningOver=12.1",
    f"{base}&fromInningOver=12.6",
    f"{base}&fromInningOver=13",
    f"{base}&fromInningOver=11",
    f"{base}&fromInningOver=12&inningNumber=2",
    f"lang=en&seriesId=1387592&matchId=1387599&inningNumber=2",
]

for params in tests:
    status, text = api_get(params)
    print(f"[{status}] {params} -> {text[:100]}")

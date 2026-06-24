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

base = "lang=en&seriesId=1387592&matchId=1387599"

tests = [
    f"{base}",
    f"{base}&sortDirection=DESC",
    f"{base}&inningNumber=1",
    f"{base}&inningNumber=2",
    f"{base}&commentType=ALL",
    f"{base}&inningNumber=2&commentType=ALL",
    f"{base}&inningNumber=2&commentType=ALL&sortDirection=DESC",
    f"{base}&sortDirection=DESC&fromInningOver=12",
    f"{base}&inningNumber=2&commentType=ALL&sortDirection=DESC&fromInningOver=12",
    f"{base}&fromInningOver=12",
]

print(f"Testing match commentary API parameters:")
for params in tests:
    status, text = api_get(params)
    if status == 200:
        data = __import__("json").loads(text)
        comments = data.get("content", {}).get("comments", [])
        next_ov = data.get("content", {}).get("nextInningOver")
        print(f"[{status}] {params} -> {len(comments)} comments, next={next_ov}")
    else:
        print(f"[{status}] {params} -> {text[:100]}")

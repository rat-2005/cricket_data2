"""Test POST request for commentary."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def api_post(path, body):
    tok = token(path)
    r = requests.post(
        f"https://hs-consumer-api.cricinfo.com{path}",
        headers={
            "x-hsci-auth-token": tok,
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json=body,
        impersonate="chrome"
    )
    return r.status_code, r.text

path = "/v1/pages/match/commentary"
body = {
    "lang": "en",
    "seriesId": 1387592,
    "matchId": 1387599,
    "inningNumber": 2,
    "sortDirection": "DESC",
    "fromInningOver": 12,
}

print(f"Testing POST to {path}")
status, text = api_post(path, body)
print(f"Status: {status}")
if status == 200:
    data = json.loads(text)
    comments = data.get("content", {}).get("comments", [])
    print(f"Comments: {len(comments)}")
else:
    print(f"Error: {text[:200]}")

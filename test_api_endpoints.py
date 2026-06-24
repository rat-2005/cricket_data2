"""Check if the API endpoint path is different for pagination."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

s = requests.Session(impersonate="chrome")

def try_api(path, label=""):
    tok = token(path)
    r = s.get(
        f"https://hs-consumer-api.cricinfo.com{path}",
        headers={
            "x-hsci-auth-token": tok,
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
            "Accept": "application/json",
        }
    )
    if r.status_code == 200:
        data = r.json()
        keys = list(data.keys())
        comments = data.get("comments", [])
        print(f"OK [{label}]: keys={keys[:8]}, comments={len(comments)}")
        if not comments and data:
            # Print first 500 chars of response for debugging
            print(f"  Response preview: {json.dumps(data)[:500]}")
        return data
    else:
        print(f"FAIL {r.status_code} [{label}]: {r.text[:200]}")
        return None

# Try different API endpoint patterns
# The match/commentary might not be the right endpoint for historical data
endpoints = [
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599",
    "/v1/pages/match/scorecard?lang=en&seriesId=1387592&matchId=1387599",
    "/v1/pages/match/details?lang=en&seriesId=1387592&matchId=1387599",
    "/v1/pages/match/home?lang=en&seriesId=1387592&matchId=1387599",
    "/v1/pages/match/overs-comparison?lang=en&seriesId=1387592&matchId=1387599",
    # Try without lang
    "/v1/pages/match/commentary?seriesId=1387592&matchId=1387599",
]

for ep in endpoints:
    label = ep.split("match/")[1].split("?")[0]
    try_api(ep, label)
    print()

"""Try hitting the commentary API with sortDirection as a path segment instead of query."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def api_get(path):
    s = requests.Session(impersonate="chrome")
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
    return r

# Try a recent IPL 2025 match that definitely has commentary
# CSK vs MI 2025 (if exists), or try a known recent match
# Let's try different match IDs to find one with data
test_matches = [
    # IPL 2025
    ("1449082", "1473474"),  # IPL 2025 first match guess
    # T20 World Cup 2024
    ("1411166", "1415727"),  # IND vs PAK T20WC 2024
    # IPL 2024 
    ("1410320", "1422119"),  # IPL 2024 first match
    # SA vs IND 3rd T20I (our test match)
    ("1387592", "1387599"),
    # Try a very recent match
    ("1422602", "1422610"),  # BGT 2024-25
]

for series_id, match_id in test_matches:
    path = f"/v1/pages/match/commentary?lang=en&seriesId={series_id}&matchId={match_id}&sortDirection=DESC"
    r = api_get(path)
    if r.status_code == 200:
        data = r.json()
        comments = data.get("content", {}).get("comments", data.get("comments", []))
        next_over = data.get("content", {}).get("nextInningOver", data.get("nextInningOver"))
        curr_inn = data.get("content", {}).get("currentInningNumber", data.get("currentInningNumber"))
        match_title = data.get("match", {}).get("title", "Unknown")
        match_slug = data.get("match", {}).get("slug", "Unknown")
        print(f"Match {match_id} ({match_slug}): {r.status_code}, comments={len(comments)}, nextOver={next_over}, currInn={curr_inn}")
        
        if not comments:
            # Check if comments are nested differently
            content = data.get("content", {})
            print(f"  Content keys: {list(content.keys())}")
    else:
        print(f"Match {match_id}: {r.status_code}")

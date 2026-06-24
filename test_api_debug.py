"""Debug: Try different innings/over combinations."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

s = requests.Session(impersonate="chrome")

# Try various combinations
tests = [
    # No innings/over params
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599",
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC",
    # Explicit innings
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&inningNumber=2&sortDirection=DESC",
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&inningNumber=1&sortDirection=DESC",
    # Explicit over
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&inningNumber=2&fromInningOver=14&sortDirection=DESC",
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&inningNumber=1&fromInningOver=20&sortDirection=DESC",
    # Try ASC
    "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=ASC",
    # Try a different match (IPL 2024 match)
    "/v1/pages/match/commentary?lang=en&seriesId=1410320&matchId=1422119&sortDirection=DESC",
]

for path in tests:
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
        comments = data.get("comments", [])
        next_ov = data.get("nextInningOver")
        curr_inn = data.get("currentInningNumber")
        
        # Print path params only
        params = path.split("?")[1]
        print(f"OK: {params}")
        print(f"   comments={len(comments)}, nextOver={next_ov}, currentInn={curr_inn}")
        
        if comments:
            c = comments[0]
            line = c.get("pitchLine", "N/A")
            length = c.get("pitchLength", "N/A")
            over = c.get("oversActual", "N/A")
            print(f"   Sample: over={over}, line={line}, length={length}")
    else:
        params = path.split("?")[1]
        print(f"FAIL ({r.status_code}): {params}")

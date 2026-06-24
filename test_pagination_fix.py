"""Test pagination with fromInningOver WITHOUT inningNumber."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

s = requests.Session(impersonate="chrome")

for over in [12, 10, 8, 5, 3, 1]:
    path = f"/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver={over}"
    r = s.get(
        f"https://hs-consumer-api.cricinfo.com{path}",
        headers={
            "x-hsci-auth-token": token(path),
            "Origin": "https://www.espncricinfo.com",
            "Referer": "https://www.espncricinfo.com/",
        }
    )
    if r.status_code == 200:
        data = r.json()
        content = data.get("content", {})
        comments = content.get("comments", [])
        next_ov = content.get("nextInningOver")
        curr_inn = content.get("currentInningNumber")
        if comments:
            first_over = comments[0].get("oversActual")
            last_over = comments[-1].get("oversActual")
            first_inn = comments[0].get("inningNumber")
            last_inn = comments[-1].get("inningNumber")
            print(f"fromOver={over}: {len(comments)} comments, range=Inn{last_inn}:{last_over} to Inn{first_inn}:{first_over}, nextOver={next_ov}, currInn={curr_inn}")
        else:
            print(f"fromOver={over}: 0 comments, nextOver={next_ov}, currInn={curr_inn}")
    else:
        print(f"fromOver={over}: status {r.status_code}")

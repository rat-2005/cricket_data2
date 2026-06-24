"""Inspect the full API response structure."""
from curl_cffi import requests
import hmac, hashlib, time, json

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"

def token(path):
    t = f"exp={int(time.time())+60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

s = requests.Session(impersonate="chrome")

# Fetch scorecard (which has inningOvers with balls)
path = "/v1/pages/match/scorecard?lang=en&seriesId=1387592&matchId=1387599"
r = s.get(
    f"https://hs-consumer-api.cricinfo.com{path}",
    headers={
        "x-hsci-auth-token": token(path),
        "Origin": "https://www.espncricinfo.com",
        "Referer": "https://www.espncricinfo.com/",
    }
)
data = r.json()

# Navigate to content.innings
content = data.get("content", {})
print("Content keys:", list(content.keys()))

innings = content.get("innings", [])
print(f"Number of innings: {len(innings)}")

total_balls_all = 0
for i, inn in enumerate(innings):
    overs = inn.get("inningOvers", [])
    total_balls = sum(len(ov.get("balls", [])) for ov in overs)
    total_balls_all += total_balls
    team = inn.get("team", {}).get("longName", "Unknown")
    print(f"\nInnings {i+1} ({team}): {len(overs)} overs, {total_balls} balls")
    
    if total_balls > 0:
        for ov in overs[:2]:
            for ball in ov.get("balls", [])[:2]:
                over_num = ball.get("oversActual")
                line = ball.get("pitchLine")
                length = ball.get("pitchLength")
                shot = ball.get("shotType")
                runs = ball.get("totalRuns")
                print(f"  Over {over_num}: {line} / {length} -> {shot} ({runs} runs)")

print(f"\nTotal balls across all innings: {total_balls_all}")

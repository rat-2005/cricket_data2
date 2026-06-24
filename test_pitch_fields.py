"""Deep inspection: What pitch data fields exist in the Cricinfo SSR commentary?"""
from curl_cffi import requests
import re
import json

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>')

base = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599"

# Get the SSR commentary data
r = requests.get(f"{base}/ball-by-ball-commentary", impersonate="chrome")
m = _NEXT_DATA_RE.search(r.text)
data = json.loads(m.group(1))["props"]["appPageProps"]["data"]
content = data["content"]

# Print ALL keys of the first comment
comments = content["comments"]
print(f"Total comments in SSR: {len(comments)}")
print(f"\nALL keys in a comment: {list(comments[0].keys())}")

# Print full JSON of first comment
print(f"\n=== Full JSON of first comment ===")
print(json.dumps(comments[0], indent=2))

# Check which fields have pitch data across all comments
pitch_fields = ["pitchLine", "pitchLength", "speedKph", "wagonX", "wagonY", "wagonZone", 
                "shotType", "shotControl", "bowlerType", "batsmanPlayerId", "bowlerPlayerId"]
print(f"\n=== Pitch field availability across {len(comments)} comments ===")
for field in pitch_fields:
    values = [c.get(field) for c in comments if c.get(field) is not None and c.get(field) != 0]
    if values:
        unique_vals = set(str(v) for v in values[:10])
        print(f"  {field}: {len(values)}/{len(comments)} non-empty. Samples: {unique_vals}")
    else:
        print(f"  {field}: EMPTY (all None/0)")

# Also check the full scorecard SSR for pitch data
print(f"\n=== Now checking full-scorecard SSR ===")
r2 = requests.get(f"{base}/full-scorecard", impersonate="chrome")
m2 = _NEXT_DATA_RE.search(r2.text)
data2 = json.loads(m2.group(1))["props"]["appPageProps"]["data"]

innings = data2["content"]["innings"]
for i, inn in enumerate(innings):
    overs = inn.get("inningOvers", [])
    total_balls = sum(len(ov.get("balls", [])) for ov in overs)
    print(f"\nInnings {i+1}: {len(overs)} overs, {total_balls} balls")
    if overs and overs[0].get("balls"):
        ball = overs[0]["balls"][0]
        print(f"  Ball keys: {list(ball.keys())}")
        for field in pitch_fields:
            val = ball.get(field)
            if val is not None:
                print(f"  {field}: {val}")

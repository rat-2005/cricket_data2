"""The same-origin API proxy works! Let's explore it."""
from curl_cffi import requests
import json

session = requests.Session(impersonate="chrome")

# First load a page to get cookies
r0 = session.get("https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary")
print(f"Page load: {r0.status_code}")

# Test the same-origin proxy
print("\n=== Testing same-origin API proxy ===")
base_api = "https://www.espncricinfo.com/api/match/commentary"

# Try different params
urls = [
    f"{base_api}?seriesId=1387592&matchId=1387599",
    f"{base_api}?seriesId=1387592&matchId=1387599&sortDirection=DESC",
    f"{base_api}?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC",
    f"{base_api}?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=10",
    f"{base_api}?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=5&inningNumber=2",
    f"{base_api}?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=1&inningNumber=1",
]

for url in urls:
    r = session.get(url)
    params_part = url.split("commentary")[1]
    print(f"\n{params_part}")
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            comments = data.get("comments", [])
            next_over = data.get("nextInningOver")
            current_inn = data.get("currentInningNumber")
            print(f"  Comments: {len(comments)}")
            print(f"  nextInningOver: {next_over}, currentInningNumber: {current_inn}")
            if comments:
                overs = [c.get("oversActual") for c in comments]
                inns = [c.get("inningNumber") for c in comments]
                print(f"  Innings: {set(inns)}, Over range: {min(overs)}-{max(overs)}")
                # Check for pitch data
                sample = comments[0]
                print(f"  pitchLine: {sample.get('pitchLine')}, pitchLength: {sample.get('pitchLength')}")
        except Exception as e:
            print(f"  Not JSON: {r.text[:200]}")
    else:
        print(f"  {r.text[:200]}")

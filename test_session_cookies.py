"""Use curl_cffi session: load HTML page first to get cookies, then hit API."""
from curl_cffi import requests
import json

session = requests.Session(impersonate="chrome")

# Step 1: Load the main page to get Akamai cookies
print("Step 1: Loading main page to establish session cookies...")
r1 = session.get("https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary")
print(f"  Page status: {r1.status_code}")

# Print cookies we got
print(f"  Cookies: {list(session.cookies.keys())}")

# Step 2: Try to hit the API with same session (cookies should carry over)
print("\nStep 2: Hitting API with session cookies...")
api_url = "https://hs-consumer-api.cricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=1"
headers = {
    "Origin": "https://www.espncricinfo.com",
    "Referer": "https://www.espncricinfo.com/",
    "Accept": "application/json",
}
r2 = session.get(api_url, headers=headers)
print(f"  API status: {r2.status_code}")

if r2.status_code == 200:
    data = r2.json()
    comments = data.get("comments", [])
    print(f"  SUCCESS! Got {len(comments)} comments from API!")
else:
    print(f"  Response: {r2.text[:300]}")
    
# Step 3: Try with a different API domain pattern
print("\nStep 3: Trying alternative API patterns...")

# Maybe there's a same-origin API proxy
alt_urls = [
    "https://www.espncricinfo.com/api/match/commentary?seriesId=1387592&matchId=1387599",
    "https://www.espncricinfo.com/_next/data/commentary?seriesId=1387592&matchId=1387599",
    "https://hs-consumer-api.espncricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599",
]
for url in alt_urls:
    r = session.get(url)
    print(f"  {url.split('.com')[1][:60]}... -> {r.status_code}")

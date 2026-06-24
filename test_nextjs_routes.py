"""Test Next.js data routes and alternative API endpoints."""
from curl_cffi import requests
import re
import json

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>')

# First get the buildId from the page
base = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599"
r = requests.get(f"{base}/ball-by-ball-commentary", impersonate="chrome")
m = _NEXT_DATA_RE.search(r.text)
data = json.loads(m.group(1))
build_id = data.get("buildId", "unknown")
print(f"Build ID: {build_id}")

# Check if the page has runtimeConfig with API info
runtime = data.get("runtimeConfig", {})
print(f"Runtime config keys: {list(runtime.keys())[:10]}")

# Test Next.js _next/data route (this is how Next.js does client-side navigation)
print("\n=== Test: Next.js _next/data route ===")
next_data_url = f"https://www.espncricinfo.com/_next/data/{build_id}/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary.json"
print(f"URL: {next_data_url}")
r2 = requests.get(next_data_url, impersonate="chrome")
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    try:
        d2 = r2.json()
        comments = d2.get("pageProps", {}).get("appPageProps", {}).get("data", {}).get("content", {}).get("comments", [])
        print(f"Comments via _next/data: {len(comments)}")
    except:
        print("Not JSON")
        print(r2.text[:200])

# Test: Try the hs-consumer-api with curl_cffi and proper headers  
print("\n=== Test: hs-consumer-api with Referer/Origin headers ===")
api_url = "https://hs-consumer-api.cricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC&fromInningOver=1"
headers = {
    "Origin": "https://www.espncricinfo.com",
    "Referer": "https://www.espncricinfo.com/",
    "Accept": "application/json",
}
r3 = requests.get(api_url, impersonate="chrome", headers=headers)
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    d3 = r3.json()
    comments = d3.get("comments", [])
    print(f"Comments: {len(comments)}")
else:
    print(r3.text[:200])

# Test: Try the site.api.espn.com with a different league ID
print("\n=== Test: ESPN playbyplay with league 28 (international cricket) ===")
for league in [28, 8048, 8676, 1387592]:
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/{league}/playbyplay?event=1387599&page=1"
    r4 = requests.get(url, impersonate="chrome")
    if r4.status_code == 200:
        d4 = r4.json()
        items = d4.get("commentary", {}).get("items", [])
        print(f"  League {league}: {r4.status_code} - {len(items)} items")
        if items:
            print(f"    Keys: {list(items[0].keys())[:10]}")
            break
    else:
        print(f"  League {league}: {r4.status_code}")

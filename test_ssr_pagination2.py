"""Test SSR commentary pagination using different URL patterns."""
from curl_cffi import requests
import re
import json

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>')

session = requests.Session(impersonate="chrome")

base = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599"

def fetch_comments(url):
    r = session.get(url)
    if r.status_code != 200:
        return None, None, None
    m = _NEXT_DATA_RE.search(r.text)
    if not m:
        return None, None, None
    data = json.loads(m.group(1))["props"]["appPageProps"]["data"]
    content = data.get("content", {})
    comments = content.get("comments", [])
    next_over = content.get("nextInningOver")
    current_inn = content.get("currentInningNumber")
    return comments, next_over, current_inn

# Try different URL patterns for pagination
patterns = [
    # Standard first page (innings 2, latest overs)
    f"{base}/ball-by-ball-commentary",
    # Try innings number in path
    f"{base}/ball-by-ball-commentary?innings=1",
    f"{base}/ball-by-ball-commentary?innings=2",
    # Try fromInningOver combined with innings
    f"{base}/ball-by-ball-commentary?innings=2&fromInningOver=12",
    f"{base}/ball-by-ball-commentary?innings=2&fromInningOver=10",
    f"{base}/ball-by-ball-commentary?innings=2&fromInningOver=5",
    f"{base}/ball-by-ball-commentary?innings=2&fromInningOver=1",
    f"{base}/ball-by-ball-commentary?innings=1&fromInningOver=20",
    f"{base}/ball-by-ball-commentary?innings=1&fromInningOver=1",
    # Try sortDirection
    f"{base}/ball-by-ball-commentary?sortDirection=ASC",
]

for url in patterns:
    comments, next_over, current_inn = fetch_comments(url)
    if comments:
        overs = [c.get("oversActual") for c in comments]
        inns = [c.get("inningNumber") for c in comments]
        print(f"URL: ...{url.split('commentary')[1] or '/'}")
        print(f"  Comments: {len(comments)}, inn: {set(inns)}, overs: {min(overs)}-{max(overs)}, nextOver: {next_over}, currentInn: {current_inn}")
    else:
        print(f"URL: ...{url.split('commentary')[1] or '/'}")
        print(f"  FAILED")

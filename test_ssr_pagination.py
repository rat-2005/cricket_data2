"""Test if we can paginate the ball-by-ball commentary SSR page using URL params."""
from curl_cffi import requests
import re
import json

_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>')

def fetch_commentary_page(url):
    r = requests.get(url, impersonate="chrome")
    if r.status_code != 200:
        print(f"  Status: {r.status_code}")
        return None
    m = _NEXT_DATA_RE.search(r.text)
    if not m:
        print("  No __NEXT_DATA__ found")
        return None
    return json.loads(m.group(1))["props"]["appPageProps"]["data"]

base = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599"

# Test 1: Basic commentary page
print("=== Test 1: Basic ball-by-ball-commentary ===")
data = fetch_commentary_page(f"{base}/ball-by-ball-commentary")
if data:
    content = data.get("content", {})
    comments = content.get("comments", [])
    next_over = content.get("nextInningOver")
    current_inn = content.get("currentInningNumber")
    print(f"  Comments: {len(comments)}")
    print(f"  nextInningOver: {next_over}")
    print(f"  currentInningNumber: {current_inn}")
    if comments:
        first = comments[0]
        last = comments[-1]
        print(f"  First comment over: {first.get('oversActual')} inn: {first.get('inningNumber')}")
        print(f"  Last comment over: {last.get('oversActual')} inn: {last.get('inningNumber')}")
        print(f"  Sample keys: {list(first.keys())[:15]}")

# Test 2: Try pagination with query params
print("\n=== Test 2: With ?inningNumber=1&commentPage=2 ===")
data2 = fetch_commentary_page(f"{base}/ball-by-ball-commentary?inningNumber=1&commentPage=2")
if data2:
    comments2 = data2.get("content", {}).get("comments", [])
    print(f"  Comments: {len(comments2)}")
    if comments2:
        print(f"  First over: {comments2[0].get('oversActual')} inn: {comments2[0].get('inningNumber')}")
        print(f"  Last over: {comments2[-1].get('oversActual')} inn: {comments2[-1].get('inningNumber')}")

# Test 3: Try with fromInningOver param
print("\n=== Test 3: With ?fromInningOver=1 ===")
data3 = fetch_commentary_page(f"{base}/ball-by-ball-commentary?fromInningOver=1")
if data3:
    comments3 = data3.get("content", {}).get("comments", [])
    print(f"  Comments: {len(comments3)}")
    if comments3:
        print(f"  First over: {comments3[0].get('oversActual')} inn: {comments3[0].get('inningNumber')}")
        print(f"  Last over: {comments3[-1].get('oversActual')} inn: {comments3[-1].get('inningNumber')}")

# Test 4: Try with page param
print("\n=== Test 4: With ?page=2 ===")
data4 = fetch_commentary_page(f"{base}/ball-by-ball-commentary?page=2")
if data4:
    comments4 = data4.get("content", {}).get("comments", [])
    print(f"  Comments: {len(comments4)}")
    if comments4:
        print(f"  First over: {comments4[0].get('oversActual')} inn: {comments4[0].get('inningNumber')}")
        print(f"  Last over: {comments4[-1].get('oversActual')} inn: {comments4[-1].get('inningNumber')}")

# Test 5: Try innings/1 path  
print("\n=== Test 5: innings/1 path ===")
data5 = fetch_commentary_page(f"{base}/ball-by-ball-commentary/innings/1")
if data5:
    comments5 = data5.get("content", {}).get("comments", [])
    print(f"  Comments: {len(comments5)}")
    if comments5:
        print(f"  First over: {comments5[0].get('oversActual')} inn: {comments5[0].get('inningNumber')}")
        print(f"  Last over: {comments5[-1].get('oversActual')} inn: {comments5[-1].get('inningNumber')}")

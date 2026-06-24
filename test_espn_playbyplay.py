"""ESPN playbyplay API - league 8048 works! Check for pitch data and paginate."""
from curl_cffi import requests
import json

def fetch_playbyplay(match_id, page=1):
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/8048/playbyplay?event={match_id}&page={page}"
    r = requests.get(url, impersonate="chrome")
    if r.status_code != 200:
        return None
    return r.json()

# Fetch page 1
print("=== Page 1 ===")
data = fetch_playbyplay(1387599, 1)
commentary = data.get("commentary", {})
items = commentary.get("items", [])
page_count = commentary.get("pageCount", 1)
page_index = commentary.get("pageIndex", 1)
print(f"Items: {len(items)}, pageCount: {page_count}, pageIndex: {page_index}")

if items:
    sample = items[0]
    print(f"\nFull keys in a ball item: {list(sample.keys())}")
    print(f"\nFull sample ball JSON:")
    print(json.dumps(sample, indent=2)[:2000])
    
    # Check for pitch-related keys anywhere in the data
    def find_pitch_keys(obj, prefix=""):
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if any(word in k.lower() for word in ["pitch", "line", "length", "wagon", "speed", "shot"]):
                    results.append((full_key, v))
                results.extend(find_pitch_keys(v, full_key))
        elif isinstance(obj, list) and obj:
            results.extend(find_pitch_keys(obj[0], f"{prefix}[0]"))
        return results
    
    pitch_keys = find_pitch_keys(sample)
    print(f"\nPitch-related keys found: {pitch_keys}")

# Paginate through all pages
print(f"\n=== Pagination: Total pages = {page_count} ===")
total_balls = len(items)
for p in range(2, min(page_count + 1, 5)):  # limit to 4 pages for test
    d = fetch_playbyplay(1387599, p)
    if d:
        items_p = d.get("commentary", {}).get("items", [])
        total_balls += len(items_p)
        print(f"Page {p}: {len(items_p)} items")
        if items_p:
            print(f"  First: over {items_p[0].get('over', {}).get('overs')} inn {items_p[0].get('period')}")
            print(f"  Last:  over {items_p[-1].get('over', {}).get('overs')} inn {items_p[-1].get('period')}")

print(f"\nTotal balls fetched so far: {total_balls}")

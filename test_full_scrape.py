import os
import json
import time
import hmac
import hashlib
from curl_cffi import requests

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
BASE_URL = "https://hs-consumer-api.cricinfo.com"

def get_auth_token(path):
    t = f"exp={int(time.time()) + 60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def fetch_commentary_page(series_id, match_id, inning_number=None, from_inning_over=None):
    if from_inning_over is None and inning_number is None:
        # First page uses /commentary
        path = f"/v1/pages/match/commentary?lang=en&seriesId={series_id}&matchId={match_id}&sortDirection=DESC"
    else:
        # Pagination uses /comments
        path = f"/v1/pages/match/comments?lang=en&seriesId={series_id}&matchId={match_id}&inningNumber={inning_number}&commentType=ALL&sortDirection=DESC"
        if from_inning_over is not None:
            path += f"&fromInningOver={from_inning_over}"

    headers = {
        "x-hsci-auth-token": get_auth_token(path),
        "Origin": "https://www.espncricinfo.com",
        "Referer": "https://www.espncricinfo.com/",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(f"{BASE_URL}{path}", headers=headers, impersonate="chrome")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"API Error {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def scrape_match(series_id, match_id):
    print(f"Starting scrape for Match {match_id} in Series {series_id}...")
    
    output_dir = os.path.join("data", "cricinfo_json")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Fetch initial commentary page
    first_data = fetch_commentary_page(series_id, match_id)
    if not first_data:
        print("Failed to fetch initial page.")
        return
        
    match_metadata = first_data.get("match", {})
    content_info = first_data.get("content", {})
    innings_list = content_info.get("innings", [])
    
    all_comments = []
    
    if not innings_list:
        print("No innings data found.")
        return
        
    total_innings = len(innings_list)
    
    for inning_num in range(1, total_innings + 1):
        print(f"\n--- Scraping Inning {inning_num} ---")
        
        next_over = None
        page = 1
        
        while True:
            print(f"Fetching page {page} for inning {inning_num} (fromInningOver={next_over})...")
            data = fetch_commentary_page(series_id, match_id, inning_number=inning_num, from_inning_over=next_over)
            
            if not data:
                break
                
            if 'comments' in data:
                comments = data['comments']
                next_over_val = data.get('nextInningOver')
            else:
                content = data.get("content", {})
                comments = content.get("comments", [])
                next_over_val = content.get("nextInningOver")
                
            if not comments:
                break
                
            all_comments.extend(comments)
                
            if next_over_val is None:
                break
                
            next_over = next_over_val
            page += 1
            time.sleep(0.5) 
            
    # STITCH IT ALL TOGETHER
    final_output = {
        "match": match_metadata,
        "innings": innings_list,
        "comments": all_comments
    }
    
    final_file = os.path.join(output_dir, f"match_{match_id}_complete.json")
    with open(final_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\n============================================================")
    print(f"Successfully stitched all pages together!")
    print(f"Saved {len(all_comments)} comments and match metadata to: {final_file}")

if __name__ == "__main__":
    scrape_match(1387592, 1387599)

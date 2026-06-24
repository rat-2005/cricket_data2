import os
import json
import time
import pandas as pd
import time
import hmac
import hashlib
import asyncio
import argparse
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
BASE_URL = "https://hs-consumer-api.cricinfo.com"
OUTPUT_DIR = os.path.join("data", "cricinfo_parquet")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_auth_token(path):
    t = f"exp={int(time.time()) + 60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def get_all_match_ids():
    """Load match IDs from events.json."""
    match_ids = []
    events_path = "events.json"
    if not os.path.exists(events_path):
        print("events.json not found!")
        return []
        
    with open(events_path, "r", encoding="utf-8") as f:
        urls = json.load(f)
        for url in urls:
            try:
                # URL format: http://core.espnuk.org/v2/sports/cricket/leagues/1496564/events/1496582
                match_id = url.split('/')[-1]
                match_ids.append(match_id)
            except Exception:
                pass
    return list(set(match_ids))

def log_failed_match(match_id):
    with open("failed_matches.txt", "a") as f:
        f.write(f"{match_id}\n")

async def resolve_series_id(session, match_id):
    """Hits the redirect URL to find the series_id for a given match_id."""
    url = f"https://www.espncricinfo.com/ci/engine/match/{match_id}.html"
    try:
        r = await session.get(url, allow_redirects=True)
        final_url = r.url
        # Format: https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/...
        parts = final_url.split('/')
        for part in parts:
            if '-' in part and part.split('-')[-1].isdigit():
                possible_id = part.split('-')[-1]
                if "series" in final_url and possible_id != match_id:
                    # Very basic heuristic: The series ID is usually the one before the match ID part.
                    # A better way is using regex: /series/[^/]+-(\d+)/
                    import re
                    match = re.search(r'/series/[^/]+-(\d+)/', final_url)
                    if match:
                        return match.group(1)
        return None
    except Exception as e:
        print(f"[{match_id}] Failed to resolve series ID: {e}")
        return None

async def fetch_page(session, series_id, match_id, inning_number=None, from_inning_over=None, retries=3):
    if from_inning_over is None and inning_number is None:
        path = f"/v1/pages/match/commentary?lang=en&seriesId={series_id}&matchId={match_id}&sortDirection=DESC"
    else:
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

    for attempt in range(retries):
        try:
            r = await session.get(f"{BASE_URL}{path}", headers=headers)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None # Match probably doesn't have commentary
            else:
                print(f"[{match_id}] API Error {r.status_code} on attempt {attempt+1}")
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            print(f"[{match_id}] Request failed on attempt {attempt+1}: {e}")
            await asyncio.sleep(2 ** attempt)
            
    return None

async def process_match(session, match_id):
    final_file = os.path.join(OUTPUT_DIR, f"match_{match_id}_complete.parquet")
    if os.path.exists(final_file):
        return True # Skip
        
    series_id = await resolve_series_id(session, match_id)
    if not series_id:
        print(f"[{match_id}] Could not resolve series_id. Skipping.")
        return False
        
    first_data = await fetch_page(session, series_id, match_id)
    if not first_data:
        print(f"[{match_id}] No initial commentary data found.")
        return False
        
    match_metadata = first_data.get("match", {})
    
    # Fast filtering for incomplete matches
    state = match_metadata.get("state")
    stage = match_metadata.get("stage")
    if state != "POST" and stage != "FINISHED":
        print(f"[{match_id}] Match not completed yet (state: {state}, stage: {stage}). Skipping safely.")
        return True # Safe skip, don't mark as failed
        
    content_info = first_data.get("content", {})
    innings_list = content_info.get("innings", [])
    
    if not innings_list:
        print(f"[{match_id}] No innings list. Saving metadata only.")
        # Create an empty dataframe with match_id just to mark as done
        df = pd.DataFrame([{"match_id": match_id, "empty": True}])
        df.to_parquet(final_file, index=False)
        return True
        
    all_comments = []
    
    for inning_num in range(1, len(innings_list) + 1):
        next_over = None
        while True:
            data = await fetch_page(session, series_id, match_id, inning_number=inning_num, from_inning_over=next_over)
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
            await asyncio.sleep(0.05) # Rate limit per match thread
            
    # Convert to Parquet
    if all_comments:
        df = pd.DataFrame(all_comments)
        df["match_id"] = match_id
        
        # We need to drop complex nested dict/list columns or cast them to string so Parquet can handle them
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].astype(str)
                
        df.to_parquet(final_file, index=False)
    else:
        df = pd.DataFrame([{"match_id": match_id, "empty": True}])
        df.to_parquet(final_file, index=False)
        
    print(f"[{match_id}] Scraped successfully ({len(all_comments)} comments).")
    return True

async def worker(name, queue, session):
    while True:
        match_id = await queue.get()
        try:
            success = await process_match(session, match_id)
            if not success:
                log_failed_match(match_id)
        except Exception as e:
            print(f"Worker {name} failed on {match_id}: {e}")
            log_failed_match(match_id)
        finally:
            queue.task_done()
            await asyncio.sleep(0.1) # Base delay between matches

async def main(limit=None):
    match_ids = get_all_match_ids()
    print(f"Found {len(match_ids)} total matches from events.json.")
    
    # Filter out already downloaded
    existing = set([f.split('_')[1] for f in os.listdir(OUTPUT_DIR) if f.endswith('.parquet')])
    
    # Load previously failed matches if they exist to force retry them
    failed_matches = set()
    if os.path.exists("failed_matches.txt"):
        with open("failed_matches.txt", "r") as f:
            failed_matches = set(line.strip() for line in f if line.strip())
            
    # Remove existing files unless they failed previously
    pending = [m for m in match_ids if str(m) not in existing or str(m) in failed_matches]
    
    # Clear the failed_matches file since we are retrying them now
    if os.path.exists("failed_matches.txt"):
        os.remove("failed_matches.txt")
        
    print(f"{len(existing)} already downloaded. {len(pending)} remaining (including retries).")
    
    if limit:
        pending = pending[:limit]
        print(f"Limiting to {limit} matches for this run.")
        
    queue = asyncio.Queue()
    for m in pending:
        queue.put_nowait(m)
        
    # Start workers
    num_workers = 600 # Reduced to 100 to prevent Akamai 403 on AWS IPs
    async with requests.AsyncSession(impersonate="chrome") as session:
        workers = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(f"W{i}", queue, session))
            workers.append(task)
            
        await queue.join()
        
        for w in workers:
            w.cancel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of matches to process")
    args = parser.parse_args()
    
    asyncio.run(main(limit=args.limit))

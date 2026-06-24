import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# List of all your API keys from .env
API_KEYS = [
    os.environ.get("SPORTRADAR_API_KEY", "").strip('" '),
    os.environ.get("SPORTRADAR_API_KEY2", "").strip('" '),
    os.environ.get("SPORTRADAR_API_KEY3", "").strip('" ')
]
API_KEYS = [k for k in API_KEYS if k] # Remove empties

TARGET_TEAMS = {
    "India", "England", "Australia", "New Zealand", "South Africa", 
    "Pakistan", "West Indies", "Bangladesh", "Sri Lanka", "Afghanistan", 
    "Zimbabwe", "Ireland", "United States", "Netherlands", "Nepal"
}

OUTPUT_DIR = "d:/cricket/fresh_data/sportradar_json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0
        self.lock = asyncio.Lock()
        
    async def get_key(self):
        async with self.lock:
            key = self.keys[self.index]
            self.index = (self.index + 1) % len(self.keys)
            return key

async def fetch(session, url, key_manager, retries=3):
    for i in range(retries):
        key = await key_manager.get_key()
        full_url = f"{url}?api_key={key}"
        try:
            async with session.get(full_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    print(f"Rate limited on key. Retrying in {2**(i+1)}s...")
                    await asyncio.sleep(2 ** (i + 1))
                else:
                    print(f"Error {response.status} on {url}")
                    return None
        except Exception as e:
            print(f"Request failed: {e}")
            await asyncio.sleep(2)
    return None

async def process_date(session, date_str, key_manager, match_queue):
    url = f"https://api.sportradar.com/cricket-t2/en/schedules/{date_str}/results.json"
    data = await fetch(session, url, key_manager)
    if not data:
        return
        
    for result in data.get('results', []):
        event = result.get('sport_event', {})
        match_id = event.get('id')
        competitors = event.get('competitors', [])
        
        # Check if match involves one of the target teams
        team_names = [c.get('name') for c in competitors]
        if any(team in TARGET_TEAMS for team in team_names):
            print(f"Found target match on {date_str}: {match_id} ({' vs '.join(team_names)})")
            await match_queue.put(match_id)
            
    # Respect rate limits (3 keys = ~3 requests per second max safe rate)
    await asyncio.sleep(0.35)

async def process_match(session, match_id, key_manager):
    filepath = os.path.join(OUTPUT_DIR, f"{match_id.replace(':', '_')}.json")
    if os.path.exists(filepath):
        print(f"Skipping {match_id}, already downloaded.")
        return

    url = f"https://api.sportradar.com/cricket-t2/en/matches/{match_id}/timeline.json"
    data = await fetch(session, url, key_manager)
    
    if data:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"Successfully downloaded {match_id}")
    
    # Throttle downloading
    await asyncio.sleep(0.35)

async def match_worker(session, key_manager, match_queue):
    while True:
        match_id = await match_queue.get()
        await process_match(session, match_id, key_manager)
        match_queue.task_done()

async def main(start_date_str, end_date_str):
    if not API_KEYS:
        print("No API keys found in .env!")
        return

    print(f"Loaded {len(API_KEYS)} API keys. Ready to download.")
    key_manager = KeyManager(API_KEYS)
    match_queue = asyncio.Queue()
    
    # Create dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    dates = [(start_date + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end_date-start_date).days + 1)]
    
    async with aiohttp.ClientSession() as session:
        # Start 3 background workers to download matches concurrently
        workers = [asyncio.create_task(match_worker(session, key_manager, match_queue)) for _ in range(3)]
        
        # Phase 1: Scan dates for Match IDs
        print(f"Scanning {len(dates)} days for international matches...")
        for date_str in dates:
            await process_date(session, date_str, key_manager, match_queue)
            
        # Wait for all matches in the queue to be downloaded
        print("Finished scanning dates. Waiting for downloads to complete...")
        await match_queue.join()
        
        # Cancel workers
        for w in workers:
            w.cancel()
            
    print("All downloads complete!")

if __name__ == "__main__":
    # You can change these dates! 
    # Example: scanning the last 30 days
    import sys
    if len(sys.argv) == 3:
        start = sys.argv[1]
        end = sys.argv[2]
    else:
        # Default to a small date range for testing
        start = "2023-10-01"
        end = "2023-11-19" # World Cup 2023 range
    
    asyncio.run(main(start, end))

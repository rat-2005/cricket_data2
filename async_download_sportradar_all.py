import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# List of all your API keys from .env
API_KEYS = [
    os.environ.get("SPORTRADAR_API_KEY", "").strip('" '),
    os.environ.get("SPORTRADAR_API_KEY2", "").strip('" '),
    os.environ.get("SPORTRADAR_API_KEY3", "").strip('" ')
]
API_KEYS = [k for k in API_KEYS if k] # Remove empties

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

async def fetch(session, url, key_manager, retries=5):
    for i in range(retries):
        key = await key_manager.get_key()
        full_url = f"{url}?api_key={key}"
        
        # Global Rate Limiter: Ensure we never exceed 1 req/sec across all workers to prevent IP bans
        await asyncio.sleep(1.1)
        
        try:
            async with session.get(full_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    print(f"Rate limited (429). Retrying in {2**(i+2)}s...")
                    await asyncio.sleep(2 ** (i + 2))
                elif response.status == 403:
                    # 403 often means Monthly Quota Exceeded for this key
                    print(f"WARNING: 403 Forbidden on key {key[:10]}... (Quota exceeded?)")
                    await asyncio.sleep(5)
                else:
                    print(f"Error {response.status} on {url}")
                    return None
        except Exception as e:
            print(f"Request failed: {e}")
            await asyncio.sleep(2)
    return None

async def get_all_matches(session, key_manager):
    print("Fetching master tournament list...")
    tournaments_data = await fetch(session, "https://api.sportradar.com/cricket-t2/en/tournaments.json", key_manager)
    if not tournaments_data:
        print("Failed to fetch tournaments. Check your API keys.")
        return []

    tournaments = tournaments_data.get('tournaments', [])
    print(f"Found {len(tournaments)} tournaments/tours.")

    all_match_ids = set()
    
    # We will fetch schedules sequentially to not overwhelm the API 
    # before we start the massive parallel match downloading
    for i, t in enumerate(tournaments):
        t_id = t.get('id')
        print(f"[{i+1}/{len(tournaments)}] Fetching schedule for {t.get('name')}...")
        
        schedule_data = await fetch(session, f"https://api.sportradar.com/cricket-t2/en/tournaments/{t_id}/schedule.json", key_manager)
        if not schedule_data: continue
        
        for event in schedule_data.get('sport_events', []):
            match_id = event.get('id')
            if match_id:
                all_match_ids.add(match_id)

    return list(all_match_ids)

async def process_match(session, match_id, key_manager):
    filepath = os.path.join(OUTPUT_DIR, f"{match_id.replace(':', '_')}.json")
    if os.path.exists(filepath):
        # We silently skip files we already downloaded
        return

    url = f"https://api.sportradar.com/cricket-t2/en/matches/{match_id}/timeline.json"
    data = await fetch(session, url, key_manager)
    
    if data:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"Successfully downloaded {match_id}")

async def match_worker(session, key_manager, match_queue):
    while True:
        match_id = await match_queue.get()
        await process_match(session, match_id, key_manager)
        match_queue.task_done()

async def main():
    if not API_KEYS:
        print("No API keys found in .env!")
        return

    print(f"Loaded {len(API_KEYS)} API keys. Initializing massive download pipeline...")
    key_manager = KeyManager(API_KEYS)
    
    async with aiohttp.ClientSession() as session:
        # Phase 1: Discover ALL match IDs in Sportradar history
        match_ids = await get_all_matches(session, key_manager)
        print(f"\n--- DISCOVERY COMPLETE ---")
        print(f"Found a grand total of {len(match_ids)} matches in Sportradar history.")
        
        # Filter out matches we already downloaded
        pending_matches = []
        for m_id in match_ids:
            if not os.path.exists(os.path.join(OUTPUT_DIR, f"{m_id.replace(':', '_')}.json")):
                pending_matches.append(m_id)
                
        print(f"{len(match_ids) - len(pending_matches)} matches already downloaded locally.")
        print(f"{len(pending_matches)} matches remaining to download.\n")
        
        if not pending_matches:
            print("Nothing left to download!")
            return

        # Phase 2: Massive Parallel Download
        match_queue = asyncio.Queue()
        for m_id in pending_matches:
            match_queue.put_nowait(m_id)
            
        # Start 1 background worker to download matches sequentially to avoid 429 IP Bans
        workers = [asyncio.create_task(match_worker(session, key_manager, match_queue)) for _ in range(1)]
        
        print("Starting 1 safe download worker...")
        await match_queue.join()
        
        # Cancel workers
        for w in workers:
            w.cancel()
            
    print("ALL DOWNLOADS COMPLETE!")

if __name__ == "__main__":
    asyncio.run(main())

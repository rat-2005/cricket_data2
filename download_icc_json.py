import os
import json
import asyncio
import aiohttp
import math

CLIENT_ID = "tPZJbRgIub3Vua93%2FDWtyQ%3D%3D"
OUTPUT_DIR = "d:/cricket/fresh_data/icc_json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def fetch_schedule(session, page_number):
    url = f"https://assets-icc.sportz.io/cricket/v1/schedule?client_id={CLIENT_ID}&feed_format=json&page_number={page_number}&page_size=1000"
    print(f"Fetching schedule page {page_number}...")
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', {}).get('matches', []), data.get('meta', {})
            else:
                print(f"Error fetching schedule page {page_number}: {response.status}")
                return [], {}
    except Exception as e:
        print(f"Failed to fetch schedule page {page_number}: {e}")
        return [], {}

async def download_innings(session, game_id, inning):
    url = f"https://assets-icc.sportz.io/cricket/v1/game/commentary?client_id={CLIENT_ID}&feed_format=json&game_id={game_id}&inning={inning}&lang=en&page_number=1&page_size=2000"
    
    filepath = os.path.join(OUTPUT_DIR, f"icc_game_{game_id}_inning_{inning}.json")
    if os.path.exists(filepath):
        return # Skip if already downloaded
        
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                # Check if there is actual commentary data
                inner_data = data.get('data')
                if not inner_data:
                    return # Skip if inning didn't happen
                    
                commentary = inner_data.get('Commentary', [])
                
                if not commentary:
                    return # Skip if inning didn't happen (e.g. innings 3 and 4 in T20)
                    
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                print(f"Downloaded Game {game_id} Inning {inning} ({len(commentary)} balls)")
            elif response.status != 404: # 404 is normal for missing innings
                print(f"Error {response.status} for Game {game_id} Inning {inning}")
    except Exception as e:
        print(f"Failed to fetch Game {game_id} Inning {inning}: {e}")

async def match_worker(session, match_queue):
    while True:
        game_id = await match_queue.get()
        # Fetch innings 1 through 4 simultaneously for this game
        tasks = [download_innings(session, game_id, i) for i in range(1, 5)]
        await asyncio.gather(*tasks)
        match_queue.task_done()

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Fetch entire master schedule
        print("Discovering all historical matches from ICC API...")
        master_matches = []
        first_matches, meta = await fetch_schedule(session, 1)
        master_matches.extend(first_matches)
        
        total_count = meta.get('count', 0)
        total_pages = math.ceil(total_count / 1000)
        
        print(f"Found {total_count} total matches across {total_pages} pages.")
        
        for p in range(2, total_pages + 1):
            matches, _ = await fetch_schedule(session, p)
            master_matches.extend(matches)
            
        # Save master schedule for metadata parsing later
        schedule_path = os.path.join(OUTPUT_DIR, "icc_master_schedule.json")
        with open(schedule_path, 'w', encoding='utf-8') as f:
            json.dump(master_matches, f, indent=2)
            
        print(f"Saved master metadata schedule with {len(master_matches)} matches!")
        
        # 2. Add all match IDs to the download queue
        match_queue = asyncio.Queue()
        for match in master_matches:
            match_queue.put_nowait(match.get('match_id'))
            
        # 3. Spin up multiple parallel workers to download all innings
        print(f"Starting parallel download workers for {len(master_matches)} matches...")
        num_workers = 10 # We can be more aggressive since there are no strict rate limits
        workers = [asyncio.create_task(match_worker(session, match_queue)) for _ in range(num_workers)]
        
        await match_queue.join()
        
        for w in workers:
            w.cancel()
            
    print("ALL ICC DOWNLOADS COMPLETE!")

if __name__ == "__main__":
    asyncio.run(main())

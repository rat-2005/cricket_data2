import json
import asyncio
import aiohttp

async def fetch_league_name(session, league_id, sem):
    url = f"https://sports.core.api.espn.com/v2/sports/cricket/leagues/{league_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    async with sem:
        for _ in range(3):
            try:
                async with session.get(url, headers=headers, ssl=False, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        name = data.get('name', '').lower()
                        if 'ipl' in name or 'indian premier league' in name or 'champions league' in name:
                            return league_id, data.get('name')
                        return None
                    elif resp.status in [400, 404]:
                        return None
            except Exception:
                await asyncio.sleep(1)
        return None

async def main():
    print("Loading events.json...")
    with open('events.json', 'r') as f:
        all_events = json.load(f)
        
    print(f"Total events: {len(all_events)}")
    league_ids = set([e.split('/leagues/')[1].split('/')[0] for e in all_events if '/leagues/' in e])
    print(f"Unique league IDs found in events.json: {len(league_ids)}")
    
    print("Checking ESPN for league names...")
    sem = asyncio.Semaphore(50)
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_league_name(session, lid, sem) for lid in league_ids]
        results = await asyncio.gather(*tasks)
        
    valid_leagues = [r for r in results if r is not None]
    print("\n--- FOUND IPL / CLT20 LEAGUES ---")
    for lid, name in valid_leagues:
        print(f"ID: {lid} - {name}")
        
    valid_ids = [r[0] for r in valid_leagues]
    print(f"\nFinal list of IDs: {valid_ids}")

if __name__ == '__main__':
    asyncio.run(main())

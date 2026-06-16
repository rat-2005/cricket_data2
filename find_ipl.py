import json
import asyncio
import aiohttp

async def fetch_league(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                name = data.get('name', '').lower()
                if 'ipl' in name or 'indian premier league' in name:
                    # The league ID is the last part of the URL
                    league_id = url.rstrip('/').split('/')[-1]
                    print(f"FOUND IPL ID: {league_id} ({data.get('name')})")
                    return league_id
    except:
        pass
    return None

async def main():
    with open('leagues.json', 'r') as f:
        leagues = json.load(f)
        
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_league(session, url) for url in leagues]
        results = await asyncio.gather(*tasks)
        
        ipl_ids = [r for r in results if r is not None]
        print(f"\nALL IPL IDs: {ipl_ids}")

asyncio.run(main())

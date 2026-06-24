import json
import asyncio
import aiohttp

async def fetch_league(session, url):
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                name = data.get('name', '').lower()
                if 'ipl' in name or 'indian premier league' in name:
                    print(f"FOUND IPL: {url} -> {data.get('name')}")
                    return True
    except:
        pass
    return False

async def main():
    with open('leagues.json', 'r') as f:
        leagues = json.load(f)
        
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_league(session, url) for url in leagues]
        results = await asyncio.gather(*tasks)
        if any(results):
            print("Finished.")
        else:
            print("IPL not found.")

asyncio.run(main())

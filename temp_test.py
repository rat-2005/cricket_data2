import asyncio, aiohttp, json, os

async def fetch_sample():
    async with aiohttp.ClientSession() as session:
        url = 'http://core.espnuk.org/v2/sports/cricket/leagues/1068050/events/1068417'
        async with session.get(url) as resp:
            ev = await resp.json()
            mc_url = ev['competitions'][0]['matchcards']['$ref']
        async with session.get(mc_url) as resp:
            mc = await resp.json()
            for item in mc['items']:
                if item.get('headline') == 'Batting':
                    print(json.dumps(item['playerDetails'][0], indent=2))
                    break

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fetch_sample())

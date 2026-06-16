import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('--- Player Stats MV Definition ---')
    res = await conn.fetch("SELECT pg_get_viewdef('cricket.player_stats_mv')")
    print(res[0][0])
    
    await conn.close()

asyncio.run(run())

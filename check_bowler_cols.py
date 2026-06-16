import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("SELECT * FROM cricket.bowler_stats_mv LIMIT 1")
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

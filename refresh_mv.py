import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("Refreshing Materialized Views...")
    await conn.execute("REFRESH MATERIALIZED VIEW cricket.player_stats_mv")
    await conn.execute("REFRESH MATERIALIZED VIEW cricket.bowler_stats_mv")
    print("Done!")
    
    await conn.close()

asyncio.run(run())

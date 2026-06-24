import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("SELECT COUNT(*) FROM cricket.player_match_performances")
    print("Total Player Match Performances:", res[0][0])
    
    res = await conn.fetch("SELECT COUNT(*) FROM cricket.matchcard_batting")
    print("Total Matchcard Batting Rows:", res[0][0])
    
    res = await conn.fetch("SELECT COUNT(*) FROM cricket.deliveries")
    print("Total Deliveries:", res[0][0])
    
    await conn.close()

asyncio.run(run())

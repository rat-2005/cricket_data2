import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("SELECT COUNT(*) FROM cricket.deliveries WHERE is_wide = true")
    print("Wides:", res[0][0])
    
    res = await conn.fetch("SELECT COUNT(*) FROM cricket.deliveries WHERE is_no_ball = true")
    print("No Balls:", res[0][0])
    
    await conn.close()

asyncio.run(run())

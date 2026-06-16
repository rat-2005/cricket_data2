import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT COUNT(id), COUNT(DISTINCT id) FROM cricket.deliveries 
        WHERE batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
    """)
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT runs_scored, is_wide, text, short_text
        FROM cricket.deliveries
        WHERE short_text ILIKE '%wide%' AND is_wide = false
        LIMIT 5
    """)
    print("Wides marked as is_wide=False:")
    for r in res:
        print(dict(r))
        
    res2 = await conn.fetch("""
        SELECT runs_scored, is_wide, text, short_text
        FROM cricket.deliveries
        WHERE is_wide = true
        LIMIT 5
    """)
    print("Actual wides marked as is_wide=True:")
    for r in res2:
        print(dict(r))
        
    await conn.close()

asyncio.run(run())

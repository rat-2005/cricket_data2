import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT d.runs_scored, d.is_wide, d.is_no_ball, d.is_bye, d.is_leg_bye, d.text, d.short_text
        FROM cricket.deliveries d
        WHERE d.batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
        AND d.runs_scored >= 4
        LIMIT 10
    """)
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

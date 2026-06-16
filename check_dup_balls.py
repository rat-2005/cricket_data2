import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT d.competition_id, d.over_number, d.ball_in_over, COUNT(*) as duplicates
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE d.batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
        AND c.class_name = 'ODI'
        GROUP BY d.competition_id, d.over_number, d.ball_in_over
        HAVING COUNT(*) > 1
        ORDER BY duplicates DESC
        LIMIT 10
    """)
    print("Duplicate balls in same match for Kohli:")
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

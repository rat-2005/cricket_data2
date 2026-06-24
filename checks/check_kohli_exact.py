import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT SUM(mv.total_runs) as runs, SUM(mv.balls_faced) as balls
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
    """)
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

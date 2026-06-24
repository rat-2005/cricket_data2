import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res = await conn.fetch("""
        SELECT DATE(c.date) as match_date, t1.name as team1, t2.name as team2, COUNT(*) as duplicate_count
        FROM cricket.competitions c
        JOIN cricket.competitors comp1 ON c.id = comp1.competition_id
        JOIN cricket.competitors comp2 ON c.id = comp2.competition_id
        JOIN cricket.teams t1 ON comp1.team_id = t1.id
        JOIN cricket.teams t2 ON comp2.team_id = t2.id
        WHERE comp1.id < comp2.id AND c.class_name = 'ODI'
        GROUP BY DATE(c.date), t1.name, t2.name
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        LIMIT 10
    """)
    print("Duplicate ODI matches in database:")
    for r in res:
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

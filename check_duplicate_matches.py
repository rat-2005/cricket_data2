import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # Check if there are matches with exactly the same date, teams, and venue for Virat Kohli
    res = await conn.fetch("""
        SELECT c.date, c.name, COUNT(d.id) as balls
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE d.batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
        AND c.class_name = 'ODI'
        GROUP BY c.date, c.name
        HAVING COUNT(d.id) > 100
        ORDER BY c.date
    """)
    for r in res:
        pass # print(dict(r))
        
    res2 = await conn.fetch("""
        SELECT COUNT(*), COUNT(DISTINCT c.id)
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE d.batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
        AND c.class_name = 'ODI'
    """)
    print("Total deliveries vs distinct matches for Kohli in ODIs:", dict(res2[0]))
    
    # Let's count duplicate dates
    res3 = await conn.fetch("""
        SELECT date(c.date) as match_date, COUNT(DISTINCT c.id) as num_matches
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE d.batsman_id IN (SELECT id FROM cricket.athletes WHERE full_name = 'Virat Kohli')
        AND c.class_name = 'ODI'
        GROUP BY date(c.date)
        HAVING COUNT(DISTINCT c.id) > 1
    """)
    print("Dates with multiple matches for Kohli:")
    for r in res3:
        print(dict(r))

    await conn.close()

asyncio.run(run())

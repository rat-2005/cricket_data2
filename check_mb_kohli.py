import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    res2 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(*) as innings_played
        FROM cricket.matchcard_batting mb
        JOIN cricket.competitions c ON mb.competition_id = c.id
        WHERE mb.player_name ILIKE '%Kohli%' AND c.class_name = 'ODI'
    """)
    print("matchcard_batting (ILIKE '%Kohli%'):")
    for r in res2: print(dict(r))

    res3 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(*) as innings_played
        FROM cricket.matchcard_batting mb
        JOIN cricket.competitions c ON mb.competition_id = c.id
        WHERE mb.player_name ILIKE '%Virat Kohli%' AND c.class_name = 'ODI'
    """)
    print("matchcard_batting (ILIKE '%Virat Kohli%'):")
    for r in res3: print(dict(r))
    
    res4 = await conn.fetch("""
        SELECT DISTINCT player_name FROM cricket.matchcard_batting
        WHERE player_name ILIKE '%Kohli%'
    """)
    print("Names matching Kohli:")
    for r in res4: print(dict(r))

    await conn.close()

asyncio.run(run())

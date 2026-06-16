import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("--- FROM matchcard_batting ---")
    res1 = await conn.fetch("SELECT SUM(runs) as total_runs, COUNT(DISTINCT competition_id) as matches FROM cricket.matchcard_batting WHERE player_name ILIKE '%Kohli%'")
    for r in res1: print(dict(r))
    
    print("--- FROM player_match_performances ---")
    res2 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(DISTINCT competition_id) as matches 
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        WHERE a.full_name ILIKE '%Kohli%' OR a.short_name ILIKE '%Kohli%'
    """)
    for r in res2: print(dict(r))
    
    print("--- FROM deliveries ---")
    res3 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(DISTINCT match_id) as matches 
        FROM cricket.deliveries d
        JOIN cricket.athletes a ON d.batter_id = a.id
        WHERE a.full_name ILIKE '%Kohli%' OR a.short_name ILIKE '%Kohli%'
    """)
    for r in res3: print(dict(r))
    
    await conn.close()

asyncio.run(run())

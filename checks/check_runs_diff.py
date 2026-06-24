import os, asyncio, asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("--- FROM player_match_performances (PMP) ---")
    res1 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(*) as innings_played
        FROM cricket.player_match_performances pmp
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id = c.id
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND c.class_name = 'ODI' AND pmp.is_batting = TRUE
    """)
    for r in res1: print(dict(r))

    print("--- FROM matchcard_batting ---")
    res2 = await conn.fetch("""
        SELECT SUM(runs) as total_runs, COUNT(*) as innings_played
        FROM cricket.matchcard_batting mb
        JOIN cricket.competitions c ON mb.competition_id = c.id
        WHERE mb.player_name = 'Virat Kohli' AND c.class_name = 'ODI'
    """)
    for r in res2: print(dict(r))

    print("--- FROM player_stats_mv ---")
    res3 = await conn.fetch("""
        SELECT SUM(mv.total_runs) as total_runs, COUNT(*) as matches_played
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
    """)
    for r in res3: print(dict(r))

    await conn.close()

asyncio.run(run())

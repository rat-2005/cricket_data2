import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('=== Comparing Data Sources ===\n')
    
    print('--- From player_match_performances (what MV uses) ---')
    res1 = await conn.fetch('''
        SELECT 
            a.full_name,
            c.class_name as format,
            COUNT(*) as matches,
            SUM(pmp.runs)::INT as total_runs
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id::text = c.id::text
        WHERE a.full_name = 'Virat Kohli' AND c.class_name = 'ODI' AND pmp.is_batting = true
        GROUP BY a.full_name, c.class_name
    ''')
    for r in res1: 
        print(dict(r))
    
    print('\n--- From deliveries table (source of truth) ---')
    res2 = await conn.fetch('''
        SELECT 
            a.full_name,
            c.class_name as format,
            COUNT(DISTINCT d.competition_id) as matches,
            SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 
                     WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 
                     ELSE d.runs_scored END)::INT as total_runs
        FROM cricket.deliveries d
        JOIN cricket.athletes a ON d.batsman_id = a.id
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE a.full_name = 'Virat Kohli' AND c.class_name = 'ODI'
        GROUP BY a.full_name, c.class_name
    ''')
    for r in res2: 
        print(dict(r))
    
    print('\n--- Check count of records in player_match_performances ---')
    res3 = await conn.fetch('''
        SELECT COUNT(*) as pmp_records
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND pmp.is_batting = true
    ''')
    print(dict(res3[0]))
    
    print('\n--- Check if there are duplicate matches in pmp ---')
    res4 = await conn.fetch('''
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT competition_id) as distinct_competitions
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND pmp.is_batting = true
    ''')
    print(dict(res4[0]))
    
    await conn.close()

asyncio.run(run())

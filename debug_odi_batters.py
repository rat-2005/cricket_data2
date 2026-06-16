import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('=== ODI Batters Debug ===\n')
    
    # Check what's in the MV for Virat Kohli
    print('--- Raw MV data for Virat Kohli (ODI) ---')
    res = await conn.fetch('''
        SELECT a.full_name, mv.format, mv.total_runs, mv.balls_faced
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
        ORDER BY mv.format
    ''')
    for r in res: 
        print(dict(r))
    
    print('\n--- What app query returns for Virat Kohli (ODI) ---')
    res2 = await conn.fetch('''
        SELECT 
            a.full_name, 
            SUM(mv.total_runs)::INT as total_runs, 
            SUM(mv.total_sixes)::INT as total_sixes,
            ROUND((SUM(mv.total_runs)::NUMERIC / NULLIF(SUM(mv.balls_faced), 0)) * 100, 2) as strike_rate
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
        GROUP BY a.full_name, a.image_url
    ''')
    for r in res2: 
        print(dict(r))
    
    print('\n--- Check if there are duplicate rows in the MV for Kohli ODI ---')
    res3 = await conn.fetch('''
        SELECT COUNT(*) as row_count
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
    ''')
    print(dict(res3[0]))
    
    print('\n--- Compare with raw deliveries data ---')
    res4 = await conn.fetch('''
        SELECT 
            a.full_name,
            COUNT(DISTINCT d.competition_id) as matches,
            SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 
                     WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 
                     ELSE d.runs_scored END)::INT as total_runs,
            COUNT(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE THEN 1 ELSE NULL END) as balls_faced
        FROM cricket.deliveries d
        JOIN cricket.athletes a ON d.batsman_id = a.id
        JOIN cricket.competitions c ON d.competition_id = c.id
        WHERE a.full_name = 'Virat Kohli' AND c.class_name = 'ODI'
        GROUP BY a.full_name
    ''')
    for r in res4: 
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

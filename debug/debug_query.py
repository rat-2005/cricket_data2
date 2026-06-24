import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('--- Checking bowler MV data for Adil Usman Rashid ---')
    res = await conn.fetch('''
        SELECT a.full_name, mv.format, mv.total_wickets, mv.runs_conceded, mv.overs_bowled
        FROM cricket.bowler_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Adil Usman Rashid'
        ORDER BY mv.format
    ''')
    for r in res: 
        print(dict(r))
    
    print()
    print('--- Check what app query returns for this bowler ---')
    res2 = await conn.fetch('''
        SELECT a.full_name, 
            SUM(mv.total_wickets)::INT as total_wickets, 
            SUM(mv.runs_conceded)::INT as runs_conceded,
            ROUND(SUM(mv.overs_bowled)::NUMERIC, 1) as overs_bowled
        FROM cricket.bowler_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        GROUP BY a.full_name
        HAVING a.full_name = 'Adil Usman Rashid'
    ''')
    for r in res2: 
        print(dict(r))
    
    await conn.close()

asyncio.run(run())

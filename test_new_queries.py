import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('=== Testing ODI Query ===\n')
    
    comp_filter = "WHERE class_name = 'ODI'"
    
    print('--- Testing Top Batters Query ---')
    try:
        res = await conn.fetch(f"""
            SELECT 
                a.full_name, 
                a.image_url,
                SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 
                         WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 
                         ELSE d.runs_scored END)::INT as total_runs,
                SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT as total_sixes,
                ROUND((SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 
                                 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 
                                 ELSE d.runs_scored END)::NUMERIC / NULLIF(COUNT(CASE WHEN d.is_wide=FALSE THEN 1 ELSE NULL END), 0)) * 100, 2) as strike_rate
            FROM cricket.deliveries d
            JOIN cricket.competitions c ON d.competition_id = c.id
            JOIN cricket.athletes a ON d.batsman_id = a.id
            {comp_filter}
            GROUP BY a.full_name, a.image_url
            ORDER BY total_runs DESC NULLS LAST
            LIMIT 3;
        """)
        for r in res:
            print(dict(r))
    except Exception as e:
        print(f"Error: {e}")
    
    print('\n--- Testing Top Bowlers Query ---')
    try:
        res = await conn.fetch(f"""
            SELECT 
                a.full_name, 
                a.image_url,
                COUNT(DISTINCT dis.delivery_id)::INT as total_wickets,
                SUM(d.runs_scored)::INT as runs_conceded,
                ROUND(COUNT(*)::NUMERIC / 6, 1) as overs_bowled,
                CASE 
                    WHEN COUNT(*) > 0 
                    THEN ROUND((SUM(d.runs_scored)::NUMERIC / (COUNT(*)::NUMERIC / 6)), 2)
                    ELSE 0.0
                END as economy
            FROM cricket.deliveries d
            JOIN cricket.competitions c ON d.competition_id = c.id
            JOIN cricket.athletes a ON d.bowler_id = a.id
            LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
            {comp_filter}
            GROUP BY a.full_name, a.image_url
            ORDER BY total_wickets DESC NULLS LAST, economy ASC NULLS LAST
            LIMIT 3;
        """)
        for r in res:
            print(dict(r))
    except Exception as e:
        print(f"Error: {e}")
    
    await conn.close()

asyncio.run(run())

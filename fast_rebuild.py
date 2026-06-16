import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("=== Fast Rebuild of player_match_performances ===\n")
    
    # Clear old data
    print("Clearing old data...")
    await conn.execute("DELETE FROM cricket.player_match_performances")
    
    # Insert batting data per match
    print("Inserting batting data (match by match)...")
    await conn.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, runs, sixes, balls_faced)
        SELECT 
            d.batsman_id::VARCHAR,
            comp.id,
            true,
            SUM(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE 
                     THEN CASE WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END
                     ELSE 0 END)::INT,
            SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT,
            COUNT(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE THEN 1 ELSE NULL END)::INT
        FROM cricket.deliveries d
        JOIN cricket.competitors comp ON d.batting_team_id::VARCHAR = comp.id::VARCHAR AND d.competition_id::text = comp.competition_id::text
        WHERE d.batsman_id IS NOT NULL
        GROUP BY d.batsman_id, comp.id
    """)
    
    # Insert bowling data per match
    print("Inserting bowling data (match by match)...")
    await conn.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, wickets, runs_conceded, overs_bowled)
        SELECT 
            d.bowler_id::VARCHAR,
            comp.id,
            false,
            COUNT(DISTINCT CASE WHEN dis.id IS NOT NULL AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') 
                                THEN dis.id ELSE NULL END)::INT,
            SUM(d.runs_scored)::INT,
            ROUND(COUNT(*)::NUMERIC / 6, 2)::NUMERIC
        FROM cricket.deliveries d
        JOIN cricket.competitors comp ON d.bowling_team_id::VARCHAR = comp.id::VARCHAR AND d.competition_id::text = comp.competition_id::text
        LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id
        WHERE d.bowler_id IS NOT NULL
        GROUP BY d.bowler_id, comp.id
    """)
    
    total_records = await conn.fetchval("SELECT COUNT(*) FROM cricket.player_match_performances")
    print(f"✓ Inserted {total_records:,} total records\n")
    
    # Refresh MVs
    print("Refreshing materialized views...")
    await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.player_stats_mv")
    print("✓ player_stats_mv refreshed")
    await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.bowler_stats_mv")
    print("✓ bowler_stats_mv refreshed\n")
    
    # Verify
    print("=== Verification ===")
    kohli_mv = await conn.fetchrow("""
        SELECT SUM(total_runs)::INT as total_runs
        FROM cricket.player_stats_mv mv
        JOIN cricket.athletes a ON mv.athlete_id = a.id
        WHERE a.full_name = 'Virat Kohli' AND mv.format = 'ODI'
    """)
    print(f"Virat Kohli ODI runs (from MV): {kohli_mv['total_runs']}")
    
    await conn.close()
    print("\n✓ Complete!")

asyncio.run(run())

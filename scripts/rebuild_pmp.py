import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("=== Rebuilding player_match_performances from deliveries ===\n")
    
    # First, clear the old incomplete data
    print("Clearing old player_match_performances data...")
    await conn.execute("DELETE FROM cricket.player_match_performances")
    print("✓ Cleared\n")
    
    # Rebuild batting statistics
    print("Rebuilding batting statistics...")
    await conn.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, runs, sixes, balls_faced)
        SELECT DISTINCT
            d.batsman_id::VARCHAR as athlete_id,
            comp.id as competitor_id,
            true as is_batting,
            SUM(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE 
                     THEN CASE WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END
                     ELSE 0 END)::INT as runs,
            SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT as sixes,
            COUNT(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE THEN 1 ELSE NULL END)::INT as balls_faced
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        JOIN cricket.competitors comp ON d.batting_team_id::VARCHAR = comp.id::VARCHAR AND d.competition_id::text = comp.competition_id::text
        WHERE d.batsman_id IS NOT NULL
        GROUP BY d.batsman_id, comp.id, d.competition_id
    """)
    bat_count = await conn.fetchval("SELECT COUNT(*) FROM cricket.player_match_performances WHERE is_batting = true")
    print(f"✓ Inserted {bat_count:,} batting records\n")
    
    # Rebuild bowling statistics
    print("Rebuilding bowling statistics...")
    await conn.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, wickets, runs_conceded, overs_bowled)
        SELECT DISTINCT
            d.bowler_id::VARCHAR as athlete_id,
            comp.id as competitor_id,
            false as is_batting,
            COUNT(DISTINCT CASE WHEN dis.id IS NOT NULL AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') 
                                THEN dis.id ELSE NULL END)::INT as wickets,
            SUM(d.runs_scored)::INT as runs_conceded,
            ROUND(COUNT(*)::NUMERIC / 6, 2)::NUMERIC as overs_bowled
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id = c.id
        JOIN cricket.competitors comp ON d.bowling_team_id::VARCHAR = comp.id::VARCHAR AND d.competition_id::text = comp.competition_id::text
        LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id
        WHERE d.bowler_id IS NOT NULL
        GROUP BY d.bowler_id, comp.id, d.competition_id
    """)
    bowl_count = await conn.fetchval("SELECT COUNT(*) FROM cricket.player_match_performances WHERE is_batting = false")
    print(f"✓ Inserted {bowl_count:,} bowling records\n")
    
    # Refresh materialized views
    print("Refreshing materialized views...")
    await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.player_stats_mv")
    await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.bowler_stats_mv")
    print("✓ Materialized views refreshed\n")
    
    # Verify the data
    print("=== Verification ===")
    kohli_odi = await conn.fetchrow("""
        SELECT SUM(pmp.runs)::INT as total_runs
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id = a.id
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id::text = c.id::text
        WHERE a.full_name = 'Virat Kohli' AND c.class_name = 'ODI' AND pmp.is_batting = true
    """)
    if kohli_odi and kohli_odi['total_runs']:
        print(f"Virat Kohli ODI runs (updated): {kohli_odi['total_runs']}")
    else:
        print("Kohli ODI data not found")
    
    await conn.close()
    print("\n✓ Complete!")

asyncio.run(run())

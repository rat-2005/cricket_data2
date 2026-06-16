import os, psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    print("Step 1: Clearing player_match_performances...")
    cur.execute("DELETE FROM cricket.player_match_performances")
    deleted = cur.rowcount
    print(f"  Deleted {deleted:,} records")
    conn.commit()
    
    print("\nStep 2: Rebuilding from deliveries - BATTING STATS...")
    cur.execute("""
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
        JOIN cricket.competitors comp ON d.batting_team_id::VARCHAR = comp.id::VARCHAR 
            AND d.competition_id::text = comp.competition_id::text
        WHERE d.batsman_id IS NOT NULL
        GROUP BY d.batsman_id, comp.id
    """)
    batting_inserted = cur.rowcount
    print(f"  Inserted {batting_inserted:,} batting records")
    conn.commit()
    
    print("\nStep 3: Rebuilding from deliveries - BOWLING STATS...")
    cur.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, wickets, overs_bowled)
        SELECT 
            d.bowler_id::VARCHAR,
            comp.id,
            false,
            COUNT(DISTINCT dm.id)::INT,
            ROUND(COUNT(DISTINCT d.ball_id)/6.0, 2)::NUMERIC
        FROM cricket.deliveries d
        LEFT JOIN cricket.dismissals dm ON d.match_id = dm.match_id 
            AND d.ball_id::VARCHAR = dm.ball_number::VARCHAR
            AND d.bowler_id::VARCHAR = dm.bowler_id::VARCHAR
        JOIN cricket.competitors comp ON d.bowling_team_id::VARCHAR = comp.id::VARCHAR 
            AND d.competition_id::text = comp.competition_id::text
        WHERE d.bowler_id IS NOT NULL
        GROUP BY d.bowler_id, comp.id
    """)
    bowling_inserted = cur.rowcount
    print(f"  Inserted {bowling_inserted:,} bowling records")
    conn.commit()
    
    print("\nStep 4: Refreshing Materialized Views...")
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.player_stats_mv")
    print("  Refreshed player_stats_mv")
    conn.commit()
    
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.bowler_stats_mv")
    print("  Refreshed bowler_stats_mv")
    conn.commit()
    
    print("\n✅ Rebuild Complete!")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM cricket.player_match_performances")
    total = cur.fetchone()[0]
    print(f"\nTotal PMP records now: {total:,}")
    
    cur.execute("""
        SELECT c.class_name, SUM(pmp.runs)::INT as total_runs
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id::VARCHAR = a.id::VARCHAR
        JOIN cricket.competitors comp ON pmp.competitor_id = comp.id
        JOIN cricket.competitions c ON comp.competition_id::text = c.id::text
        WHERE a.full_name = 'Virat Kohli' AND pmp.is_batting = true
        GROUP BY c.class_name
    """)
    print("\nKohli ODI runs after rebuild:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,} runs")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

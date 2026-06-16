import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    print("Clearing player_match_performances...")
    cur.execute("DELETE FROM cricket.player_match_performances")
    conn.commit()
    
    # Build batting stats match by match
    print("Building batting stats from match data...")
    
    cur.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, runs, sixes, balls_faced)
        SELECT 
            d.batsman_id::VARCHAR,
            d.batting_team_id::INTEGER,
            true,
            SUM(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE 
                     THEN CASE WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END
                     ELSE 0 END)::INT,
            SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT,
            COUNT(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE THEN 1 ELSE NULL END)::INT
        FROM cricket.deliveries d
        WHERE d.batsman_id IS NOT NULL
        GROUP BY d.batsman_id, d.batting_team_id
    """)
    batting_inserted = cur.rowcount
    print(f"  Inserted {batting_inserted:,} batting records")
    conn.commit()
    
    # Build bowling stats
    print("\nBuilding bowling stats...")
    
    cur.execute("""
        INSERT INTO cricket.player_match_performances 
        (athlete_id, competitor_id, is_batting, wickets, overs_bowled)
        SELECT 
            d.bowler_id::VARCHAR,
            d.bowling_team_id::INTEGER,
            false,
            COUNT(DISTINCT CASE WHEN dm.id IS NOT NULL THEN dm.id END)::INT,
            ROUND(COUNT(DISTINCT d.ball_id)/6.0, 2)::NUMERIC
        FROM cricket.deliveries d
        LEFT JOIN cricket.dismissals dm ON d.match_id = dm.match_id 
            AND d.ball_id::VARCHAR = dm.ball_number::VARCHAR
            AND d.bowler_id::VARCHAR = dm.bowler_id::VARCHAR
        WHERE d.bowler_id IS NOT NULL
        GROUP BY d.bowler_id, d.bowling_team_id
    """)
    bowling_inserted = cur.rowcount
    print(f"  Inserted {bowling_inserted:,} bowling records")
    conn.commit()
    
    print("\nRefreshing materialized views...")
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.player_stats_mv")
    conn.commit()
    cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cricket.bowler_stats_mv")
    conn.commit()
    
    print("\n✅ Rebuild Complete!")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM cricket.player_match_performances")
    total = cur.fetchone()[0]
    print(f"Total PMP records: {total:,}")
    
    cur.execute("""
        SELECT 
            a.full_name,
            SUM(pmp.runs)::INT as total_runs
        FROM cricket.player_match_performances pmp
        JOIN cricket.athletes a ON pmp.athlete_id::VARCHAR = a.id::VARCHAR
        WHERE pmp.is_batting = true
        GROUP BY a.full_name
        ORDER BY total_runs DESC
        LIMIT 5
    """)
    print("\nTop 5 batters after rebuild:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,} runs")
    
except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()
    conn.rollback()
finally:
    cur.close()
    conn.close()

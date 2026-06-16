import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True  # Execute each command immediately
cur = conn.cursor()

try:
    print("Forcing drop of old materialized view...")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.player_stats_mv CASCADE")
    print("✅ Dropped")
    
    print("Creating new player_stats_mv from deliveries...")
    cur.execute("""
        CREATE MATERIALIZED VIEW cricket.player_stats_mv AS
        SELECT 
            d.batsman_id::VARCHAR as athlete_id,
            c.class_name as format,
            SUM(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE 
                     THEN CASE WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END
                     ELSE 0 END)::INT as total_runs,
            SUM(CASE WHEN d.is_boundary=TRUE AND d.runs_scored >= 6 THEN 1 ELSE 0 END)::INT as total_sixes,
            COUNT(CASE WHEN d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE THEN 1 ELSE NULL END)::INT as balls_faced
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id::text = c.id::text
        WHERE d.batsman_id IS NOT NULL
        GROUP BY d.batsman_id, c.class_name
    """)
    print("✅ Materialized view created!")
    
    print("\nVerifying data - Top ODI batters...")
    cur.execute("""
        SELECT athlete_id, total_runs 
        FROM cricket.player_stats_mv 
        WHERE format = 'ODI'
        ORDER BY total_runs DESC 
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,} runs")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()

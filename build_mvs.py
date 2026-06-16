import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
conn.autocommit = True
cur = conn.cursor()

print("Creating Materialized View for player stats...")
cur.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.player_stats_mv CASCADE;")
cur.execute("""
CREATE MATERIALIZED VIEW cricket.player_stats_mv AS
SELECT 
    d.batsman_id as athlete_id,
    c.class_name as format,
    SUM(CASE 
        WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 
        WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 
        ELSE d.runs_scored 
    END)::INT as total_runs,
    SUM(CASE 
        WHEN d.is_boundary=TRUE AND d.is_wide=FALSE AND d.is_bye=FALSE AND d.is_leg_bye=FALSE 
             AND (CASE WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) >= 6 
        THEN 1 ELSE 0 
    END)::INT as total_sixes,
    SUM(CASE WHEN d.is_wide=FALSE THEN 1 ELSE 0 END)::INT as balls_faced
FROM cricket.deliveries d
JOIN cricket.competitions c ON d.competition_id = c.id
WHERE d.batsman_id IS NOT NULL AND c.class_name IS NOT NULL
GROUP BY d.batsman_id, c.class_name;
""")
print("Created player_stats_mv!")

cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_player_stats_mv ON cricket.player_stats_mv (athlete_id, format);")

print("Creating Materialized View for bowler stats...")
cur.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.bowler_stats_mv CASCADE;")
cur.execute("""
CREATE MATERIALIZED VIEW cricket.bowler_stats_mv AS
SELECT 
    d.bowler_id as athlete_id,
    c.class_name as format,
    SUM(CASE 
        WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 
            CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END
        ELSE d.runs_scored 
    END)::INT as runs_conceded,
    CAST(TRUNC(SUM(CASE WHEN d.is_wide=FALSE AND d.is_no_ball=FALSE THEN 1 ELSE 0 END) / 6.0) + 
         (MOD(SUM(CASE WHEN d.is_wide=FALSE AND d.is_no_ball=FALSE THEN 1 ELSE 0 END), 6) / 10.0) AS NUMERIC(10,1)) as overs_bowled,
    COUNT(dis.delivery_id)::INT as total_wickets
FROM cricket.deliveries d
JOIN cricket.competitions c ON d.competition_id = c.id
LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id 
     AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
WHERE d.bowler_id IS NOT NULL AND c.class_name IS NOT NULL
GROUP BY d.bowler_id, c.class_name;
""")
print("Created bowler_stats_mv!")

cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_bowler_stats_mv ON cricket.bowler_stats_mv (athlete_id, format);")
print("Done!")

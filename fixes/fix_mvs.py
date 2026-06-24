import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

# Redefine player_stats_mv
cur.execute("""
DROP MATERIALIZED VIEW IF EXISTS cricket.player_stats_mv CASCADE;

CREATE MATERIALIZED VIEW cricket.player_stats_mv AS
WITH combined_deliveries AS (
    SELECT 
        d.batsman_id as athlete_id,
        c.class_name as format,
        d.batsman_runs,
        d.is_wide
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON c.id = d.competition_id
    
    UNION ALL
    
    SELECT 
        d.batsman_id as athlete_id,
        CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
        d.batsman_runs,
        d.is_wide
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON m.id = d.match_id
)
SELECT 
    athlete_id,
    format,
    SUM(batsman_runs)::integer as total_runs,
    SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END)::integer as total_sixes,
    COUNT(CASE WHEN is_wide = false THEN 1 ELSE NULL END)::integer as balls_faced
FROM combined_deliveries
GROUP BY athlete_id, format;

CREATE INDEX idx_player_stats_mv_athlete ON cricket.player_stats_mv(athlete_id);
CREATE INDEX idx_player_stats_mv_format ON cricket.player_stats_mv(format);
""")

# Redefine bowler_stats_mv
cur.execute("""
DROP MATERIALIZED VIEW IF EXISTS cricket.bowler_stats_mv CASCADE;

CREATE MATERIALIZED VIEW cricket.bowler_stats_mv AS
WITH combined_bowling AS (
    SELECT 
        d.bowler_id as athlete_id,
        c.class_name as format,
        CASE WHEN dis.delivery_id IS NOT NULL THEN 1 ELSE 0 END as is_wicket,
        d.bowler_conceded,
        d.bowler_overs
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON c.id = d.competition_id
    LEFT JOIN cricket.dismissals dis ON d.id = dis.delivery_id 
        AND dis.type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out')
        
    UNION ALL
    
    SELECT 
        d.bowler_id as athlete_id,
        CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
        CASE WHEN d.dismissal_type IS NOT NULL AND d.dismissal_type NOT IN ('run out', 'retired hurt', 'retired not out (hurt)', 'obstructing the field', 'retired out') THEN 1 ELSE 0 END as is_wicket,
        -- Cricsheet conceded rules
        CASE WHEN d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 
            CASE WHEN d.is_no_ball=TRUE OR d.is_wide=TRUE THEN 1 ELSE 0 END 
        ELSE d.runs_scored END as bowler_conceded,
        -- Cricsheet overs rules (1 ball = 1/6 of an over)
        CASE WHEN d.is_wide=TRUE OR d.is_no_ball=TRUE THEN 0 ELSE 1.0/6.0 END as bowler_overs
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON m.id = d.match_id
)
SELECT 
    athlete_id,
    format,
    SUM(is_wicket)::integer as total_wickets,
    SUM(bowler_conceded)::integer as runs_conceded,
    SUM(bowler_overs) as overs_bowled
FROM combined_bowling
GROUP BY athlete_id, format;

CREATE INDEX idx_bowler_stats_mv_athlete ON cricket.bowler_stats_mv(athlete_id);
CREATE INDEX idx_bowler_stats_mv_format ON cricket.bowler_stats_mv(format);
""")

conn.commit()
print("Materialized Views successfully redefined to include Cricsheet data!")

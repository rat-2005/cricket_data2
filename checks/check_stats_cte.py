import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    WITH combined_deliveries AS (
        SELECT 
            d.competition_id as match_id,
            d.batsman_runs,
            d.is_wide,
            d.is_bye,
            d.is_leg_bye
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        WHERE d.batsman_id = '253802' AND ((l.name NOT ILIKE '%world cup%' AND l.name NOT ILIKE '%world twenty20%' AND l.name NOT ILIKE '%t20 world cup%' AND l.name NOT ILIKE '%championship%' AND l.name NOT ILIKE '%asia cup%' AND l.name NOT ILIKE '%champions trophy%' AND l.name NOT ILIKE '%premier league%' AND l.name NOT ILIKE '%ipl%') OR l.name IS NULL)
    ),
    match_aggregates AS (
        SELECT 
            match_id,
            SUM(batsman_runs) as match_score,
            SUM(CASE WHEN batsman_runs = 0 AND is_wide = false AND is_bye = false AND is_leg_bye = false THEN 1 ELSE 0 END) as match_dots,
            SUM(CASE WHEN batsman_runs >= 6 THEN 1 ELSE 0 END) as match_sixes,
            SUM(CASE WHEN is_wide = false THEN 1 ELSE 0 END) as match_balls_faced
        FROM combined_deliveries
        GROUP BY match_id
    )
    SELECT 
        SUM(match_score)::integer as total_runs,
        SUM(match_sixes)::integer as total_sixes,
        SUM(match_balls_faced)::integer as balls_faced,
        MAX(match_score)::integer as highest_score,
        SUM(match_dots)::integer as dot_balls
    FROM match_aggregates
""")

print('Output:', cur.fetchone())

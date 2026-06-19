import os, json
import psycopg2, psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get("DATABASE_URL")

query = """
    WITH combined_faceoff AS (
        SELECT 
            c.class_name as format,
            l.name as league,
            d.batsman_runs,
            d.is_wide,
            d.is_no_ball as is_noball
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON c.id = d.competition_id
        LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
        LEFT JOIN cricket.leagues l ON el.league_id = l.id
        WHERE d.batsman_id = '253802' AND d.bowler_id = '26421'
        
        UNION ALL
        
        SELECT 
            CASE WHEN m.format = 'MD' THEN 'Test' ELSE m.format END as format,
            'International' as league,
            d.batsman_runs as batsman_runs,
            d.is_wide,
            d.is_no_ball as is_noball
        FROM cricket.cricsheet_deliveries d
        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
        WHERE d.batsman_id = '253802' AND d.bowler_id = '26421'
    )
    SELECT 
        format,
        league,
        SUM(batsman_runs) as runs,
        COUNT(*) FILTER (WHERE NOT is_wide AND NOT is_noball) as balls
    FROM combined_faceoff
    GROUP BY format, league
"""

with psycopg2.connect(DB_URL) as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        res = cur.fetchall()
        print(json.dumps(res, indent=2, default=str))

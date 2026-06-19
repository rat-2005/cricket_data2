import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
WITH kohli_matches AS (
    -- Main DB
    SELECT 
        'Cricinfo' as source,
        c.id as match_id,
        c.date::date as match_date,
        EXTRACT(YEAR FROM c.date) as year,
        SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) as runs
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON d.competition_id = c.id
    WHERE d.batsman_id = '253802' AND c.class_name = 'Test'
    GROUP BY c.id, c.date
    
    UNION ALL
    
    -- Cricsheet DB
    SELECT 
        'Cricsheet' as source,
        m.id as match_id,
        m.match_date as match_date,
        EXTRACT(YEAR FROM m.match_date) as year,
        SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) as runs
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON d.match_id = m.id
    WHERE d.batsman_id = '253802' AND m.format = 'Test'
    GROUP BY m.id, m.match_date
)
SELECT year, 
       SUM(CASE WHEN source = 'Cricinfo' THEN 1 ELSE 0 END) as cricinfo_matches,
       SUM(CASE WHEN source = 'Cricsheet' THEN 1 ELSE 0 END) as cricsheet_matches,
       SUM(CASE WHEN source = 'Cricinfo' THEN runs ELSE 0 END) as cricinfo_runs,
       SUM(CASE WHEN source = 'Cricsheet' THEN runs ELSE 0 END) as cricsheet_runs
FROM kohli_matches
GROUP BY year
ORDER BY year;
"""

df = pd.read_sql_query(query, conn)
print(df.to_string())

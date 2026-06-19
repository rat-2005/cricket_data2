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
        SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) as runs
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON d.match_id = m.id
    WHERE d.batsman_id = '253802' AND m.format = 'Test'
    GROUP BY m.id, m.match_date
)
SELECT * FROM kohli_matches ORDER BY match_date;
"""

df = pd.read_sql_query(query, conn)
# Check for duplicate dates
df['date_count'] = df.groupby('match_date')['match_date'].transform('count')
duplicates = df[df['date_count'] > 1]
print("Duplicates found:")
print(duplicates.to_string())

print("\nTotal runs by source:")
print(df.groupby('source')['runs'].sum())

print("\nTotal matches by source:")
print(df.groupby('source')['match_id'].count())

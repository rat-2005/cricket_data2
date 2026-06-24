import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT 
    m.id as match_id, m.match_date, SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) as runs
FROM cricket.cricsheet_deliveries d
JOIN cricket.cricsheet_matches m ON m.id = d.match_id
WHERE d.batsman_id = '28081' AND m.format = 'ODI'
GROUP BY m.id, m.match_date
"""
df = pd.read_sql_query(query, conn)
print("MS Dhoni ODI runs from Cricsheet missing matches:")
print(df)

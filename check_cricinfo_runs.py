import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT c.class_name, SUM(CASE WHEN d.is_wide=TRUE OR d.is_bye=TRUE OR d.is_leg_bye=TRUE THEN 0 WHEN d.is_no_ball=TRUE THEN d.runs_scored - 1 ELSE d.runs_scored END) as runs
FROM cricket.deliveries d
JOIN cricket.competitions c ON c.id = d.competition_id
WHERE d.batsman_id = '28081' 
GROUP BY c.class_name;
"""
df = pd.read_sql_query(query, conn)
print(df)

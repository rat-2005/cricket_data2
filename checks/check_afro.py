import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT c.id, c.date::date, c.class_name, SUM(d.runs_scored) as runs
FROM cricket.deliveries d
JOIN cricket.competitions c ON c.id = d.competition_id
WHERE d.batsman_id = '28081' AND c.date::date IN ('2007-06-06', '2007-06-09', '2007-06-10')
GROUP BY c.id, c.date::date, c.class_name;
"""
df = pd.read_sql_query(query, conn)
print(df)

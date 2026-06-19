import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT 'Cricinfo' as source, c.date::date as match_date, SUM(d.runs_scored) as runs
FROM cricket.deliveries d
JOIN cricket.competitions c ON d.competition_id = c.id
WHERE d.batsman_id = '253802' AND c.class_name = 'Test' AND EXTRACT(YEAR FROM c.date) = 2025
GROUP BY c.date
UNION ALL
SELECT 'Cricsheet' as source, m.match_date, SUM(d.runs_scored) as runs
FROM cricket.cricsheet_deliveries d
JOIN cricket.cricsheet_matches m ON d.match_id = m.id
WHERE d.batsman_id = '253802' AND m.format = 'Test' AND EXTRACT(YEAR FROM m.match_date) = 2025
GROUP BY m.match_date;
"""
df = pd.read_sql_query(query, conn)
print(df)

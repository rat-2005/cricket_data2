import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT total_runs FROM cricket.player_stats_mv 
WHERE athlete_id = '28081' AND format = 'ODI';
"""
df = pd.read_sql_query(query, conn)
print(f"Total ODI Runs for Dhoni in Materialized View: {df['total_runs'].iloc[0]}")

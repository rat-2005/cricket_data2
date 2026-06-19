import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = """
SELECT id, name FROM cricket.teams 
WHERE name IN ('India', 'Australia', 'New Zealand', 'South Africa', 'England', 'Pakistan', 'Sri Lanka', 'Bangladesh', 'West Indies', 'Afghanistan');
"""
df = pd.read_sql_query(query, conn)
print("Teams IDs:")
print(df)

cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='competitors'")
print("\nCompetitors columns:", cur.fetchall())

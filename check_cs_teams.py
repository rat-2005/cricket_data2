import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = "SELECT DISTINCT team1 FROM cricket.cricsheet_matches LIMIT 10;"
df = pd.read_sql_query(query, conn)
print("Cricsheet teams:")
print(df)

import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = "SELECT format, COUNT(*) FROM cricket.cricsheet_matches GROUP BY format;"
df = pd.read_sql_query(query, conn)
print(df)

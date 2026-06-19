import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

query = "SELECT id, full_name FROM cricket.athletes WHERE full_name ILIKE '%Dhoni%';"
df = pd.read_sql_query(query, conn)
print(df)

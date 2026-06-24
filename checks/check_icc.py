import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='cricket' AND table_name LIKE '%icc%'")
tables = [r[0] for r in cur.fetchall()]
print('icc tables:', tables)
if tables:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='cricket' AND table_name='{tables[0]}'")
    print(f'{tables[0]} columns:', [r[0] for r in cur.fetchall()])

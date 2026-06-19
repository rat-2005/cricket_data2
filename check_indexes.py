import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'deliveries'")
print("Deliveries indexes:", cur.fetchall())

cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'cricsheet_deliveries'")
print("Cricsheet deliveries indexes:", cur.fetchall())

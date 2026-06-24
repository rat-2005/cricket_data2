import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='cricket' AND table_name='deliveries'")
print('deliveries columns:', [r[0] for r in cur.fetchall()])
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='cricket' AND table_name='cricsheet_deliveries'")
print('cricsheet_deliveries columns:', [r[0] for r in cur.fetchall()])
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='cricket' AND table_name='icc_json_deliveries'")
print('icc columns:', [r[0] for r in cur.fetchall()])

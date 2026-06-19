import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM cricket.deliveries WHERE competition_id IN (SELECT id FROM cricket.cricsheet_matches);")
count = cur.fetchone()[0]
print(f"Cricsheet deliveries in main table: {count}")

cur.execute("SELECT COUNT(*) FROM cricket.cricsheet_deliveries;")
total = cur.fetchone()[0]
print(f"Total Cricsheet deliveries available: {total}")

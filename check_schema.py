import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='cricket'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='teams'")
print("Teams columns:", cur.fetchall())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='competitions'")
print("Competitions columns:", cur.fetchall())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='matchcard_teams'")
print("Matchcard teams columns:", cur.fetchall())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='cricsheet_matches'")
print("Cricsheet matches columns:", cur.fetchall())


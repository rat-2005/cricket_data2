import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

print("Truncating cricsheet tables...")
cur.execute("TRUNCATE TABLE cricket.cricsheet_matches CASCADE;")
conn.commit()
print("Tables truncated.")

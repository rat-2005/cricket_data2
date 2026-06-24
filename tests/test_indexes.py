import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'deliveries' OR tablename = 'cricsheet_deliveries'")
for r in cur.fetchall():
    print(r)

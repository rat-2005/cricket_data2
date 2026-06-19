import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='cricket' AND table_name='deliveries'")
print('\n'.join([str(r[0]) for r in cur.fetchall()]))

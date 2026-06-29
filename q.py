import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()
cursor.execute('SELECT "wagonX", "wagonY" FROM cricket.deliveries WHERE "wagonX" IS NOT NULL LIMIT 10')
for row in cursor.fetchall():
    print(row)

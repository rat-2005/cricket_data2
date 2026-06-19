import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT x_coordinate, y_coordinate, short_text, speed_kph FROM cricket.deliveries WHERE x_coordinate IS NOT NULL AND y_coordinate IS NOT NULL LIMIT 10")
rows = cur.fetchall()
for r in rows:
    print(r)

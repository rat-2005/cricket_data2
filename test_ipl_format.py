import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("""
SELECT DISTINCT class_name 
FROM cricket.competitions c
JOIN cricket.event_leagues el ON c.event_id = el.event_id
JOIN cricket.leagues l ON l.id = el.league_id
WHERE l.name = 'Indian Premier League'
""")
print(cur.fetchall())

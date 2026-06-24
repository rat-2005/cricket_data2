import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("""
    SELECT DISTINCT c.class_name
    FROM cricket.competitions c
    LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
    LEFT JOIN cricket.leagues l ON el.league_id = l.id
    WHERE l.name ILIKE '%world cup%' OR l.name ILIKE '%world twenty20%' OR l.name ILIKE '%t20 world cup%' OR l.name ILIKE '%championship%'
""")
print('ESPN Formats for World Cup:', [r[0] for r in cur.fetchall()])

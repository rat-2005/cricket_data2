import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT SUM(d.batsman_runs)
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON c.id = d.competition_id
    LEFT JOIN cricket.event_leagues el ON c.event_id = el.event_id
    LEFT JOIN cricket.leagues l ON el.league_id = l.id
    WHERE d.batter_id = 253802
    AND (l.name NOT ILIKE '%world cup%' AND l.name NOT ILIKE '%world twenty20%' AND l.name NOT ILIKE '%t20 world cup%' AND l.name NOT ILIKE '%championship%' AND l.name NOT ILIKE '%asia cup%' AND l.name NOT ILIKE '%champions trophy%' AND l.name NOT ILIKE '%premier league%' AND l.name NOT ILIKE '%ipl%' OR l.name IS NULL)
""")
print('ESPN Series Runs:', cur.fetchone()[0])

cur.execute("""
    SELECT SUM(d.batsman_runs)
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON m.id = d.match_id
    WHERE d.batter_id = 253802
""")
print('Cricsheet Series Runs:', cur.fetchone()[0])

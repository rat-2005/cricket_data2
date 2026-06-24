import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT name FROM cricket.teams WHERE name ILIKE '%England%'")
print('ESPN England teams:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT team1, team2 FROM cricket.cricsheet_matches WHERE team1 ILIKE '%England%' LIMIT 2")
print('Cricsheet England teams:', cur.fetchall())

cur.execute("""
    SELECT d.bowling_team_id 
    FROM cricket.deliveries d 
    JOIN cricket.teams t ON d.bowling_team_id = t.id 
    WHERE d.batsman_id = '253802' AND t.name ILIKE '%England%' LIMIT 2
""")
print('Deliveries vs England:', cur.fetchall())


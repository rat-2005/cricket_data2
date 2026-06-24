import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
where_d = ["d.batsman_id = '253802'"]
where_d.append("d.bowling_team_id IN (SELECT id FROM cricket.teams WHERE name ILIKE '%England%' OR abbreviation ILIKE '%England%')")
where_d.append("c.class_name IN ('ODI', 'Women''s ODI', 'Youth ODI', 'List A', 'Other OD')")

q = f"""
    SELECT SUM(d.batsman_runs)
    FROM cricket.deliveries d
    JOIN cricket.competitions c ON c.id = d.competition_id
    WHERE {' AND '.join(where_d)}
"""
print(q)
cur.execute(q)
print("ESPN Runs vs England ODI:", cur.fetchone())

where_cricsheet = ["d.batsman_id = '253802'"]
where_cricsheet.append("(m.team1 ILIKE '%England%' OR m.team2 ILIKE '%England%')")
where_cricsheet.append("m.format = 'ODI'")

qc = f"""
    SELECT SUM(d.batsman_runs)
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON m.id = d.match_id
    WHERE {' AND '.join(where_cricsheet)}
"""
cur.execute(qc)
print("Cricsheet Runs vs England ODI:", cur.fetchone())


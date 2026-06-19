import os, json
import psycopg2, psycopg2.extras
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get("DATABASE_URL")

query = """
    SELECT 
        c.class_name as format, 
        SUM(d.runs_off_bat) as runs,
        COUNT(d.id) FILTER (WHERE d.wides = 0 AND d.noballs = 0) as balls
    FROM cricket.cricsheet_deliveries d
    JOIN cricket.cricsheet_matches m ON d.match_id = m.match_id
    JOIN cricket.competitions c ON m.class_id = c.id
    WHERE d.batsman_id = 253802 AND d.bowler_id = 28081
    GROUP BY c.class_name
"""

with psycopg2.connect(DB_URL) as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query)
        res = cur.fetchall()
        print(json.dumps(res, indent=2, default=str))

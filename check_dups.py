import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

cur.execute("""
    SELECT match_id, count(*), count(DISTINCT CONCAT(match_id, '-', innings, '-', over_number, '-', ball_number))
    FROM cricket.cricsheet_deliveries 
    GROUP BY match_id 
    HAVING count(*) > 300 
    LIMIT 10
""")
print("Some matches with lots of deliveries:", cur.fetchall())

cur.execute("""
    SELECT match_id, count(*), count(DISTINCT CONCAT(match_id, '-', innings, '-', over_number, '-', ball_number))
    FROM cricket.cricsheet_deliveries 
    WHERE match_id = '1187006'
    GROUP BY match_id 
""")
print("Match 1187006 deliveries vs distinct:", cur.fetchall())


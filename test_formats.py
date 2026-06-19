import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()
cur.execute("""
SELECT DISTINCT class_name FROM cricket.competitions
""")
print("Competitions class_name:", [r[0] for r in cur.fetchall()])

cur.execute("""
SELECT DISTINCT format FROM cricket.cricsheet_matches
""")
print("Cricsheet format:", [r[0] for r in cur.fetchall()])

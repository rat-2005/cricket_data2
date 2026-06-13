import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
c = conn.cursor()

tables = ['player_match_performances', 'matchcard_batting', 'matchcard_bowling']
for t in tables:
    c.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")
    print(f"\n{t}:")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")

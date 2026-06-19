import psycopg2, os, time
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

start = time.time()
cur.execute("""
    SELECT DISTINCT bowler_id FROM cricket.deliveries WHERE batsman_id='253802' 
    UNION 
    SELECT DISTINCT bowler_id FROM cricket.cricsheet_deliveries WHERE batsman_id='253802'
""")
res = cur.fetchall()
print(f'Count: {len(res)}, Time: {time.time()-start:.3f}s')

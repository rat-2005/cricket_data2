import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

print("Checking active queries...")
cur.execute("""
    SELECT pid, state, query_start, query 
    FROM pg_stat_activity 
    WHERE state != 'idle' 
    AND pid <> pg_backend_pid();
""")

active_queries = cur.fetchall()
for q in active_queries:
    print(q)
    
print("\nKilling active queries...")
for q in active_queries:
    pid = q[0]
    print(f"Killing pid {pid}...")
    cur.execute(f"SELECT pg_terminate_backend({pid});")
    print(cur.fetchone())

conn.commit()

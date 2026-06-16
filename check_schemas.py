import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    print("Deliveries columns:")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='deliveries' ORDER BY ordinal_position LIMIT 10")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    print("\nDismissals columns:")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='cricket' AND table_name='dismissals'")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
except Exception as e:
    print(f"ERROR: {e}")
finally:
    cur.close()
    conn.close()

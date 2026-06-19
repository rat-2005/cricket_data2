import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.environ.get("DATABASE_URL")

with psycopg2.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, full_name FROM cricket.athletes WHERE full_name LIKE '%Ashwin%'")
        print(cur.fetchall())
        
        cur.execute("SELECT id, full_name FROM cricket.athletes WHERE id = '28081'")
        print("28081 is:", cur.fetchall())

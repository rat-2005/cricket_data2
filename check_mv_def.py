import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    print("Checking current player_stats_mv definition...")
    cur.execute("""
        SELECT pg_get_viewdef('cricket.player_stats_mv', true) as definition
    """)
    mv_def = cur.fetchone()[0]
    print("Current view definition:")
    print(mv_def[:500])
    
    print("\n\nChecking materialized view dependency...")
    cur.execute("SELECT * FROM cricket.player_stats_mv LIMIT 1")
    print("MV columns:", [desc[0] for desc in cur.description])
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()

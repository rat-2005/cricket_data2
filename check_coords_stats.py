import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
cur = conn.cursor()

# Check deliveries table
cur.execute("""
    SELECT 
        COUNT(*) as total_deliveries,
        COUNT(x_coordinate) as deliveries_with_coords,
        COUNT(DISTINCT competition_id) as total_matches,
        COUNT(DISTINCT CASE WHEN x_coordinate IS NOT NULL THEN competition_id END) as matches_with_coords
    FROM cricket.deliveries
""")
res = cur.fetchone()
print(f"Total Deliveries (from Cricinfo): {res[0]}")
print(f"Deliveries with coords: {res[1]}")
print(f"Total Matches: {res[2]}")
print(f"Matches with coords: {res[3]}")

# Also check cricsheet_deliveries just in case (though we saw it didn't have coords earlier, let's verify)
try:
    cur.execute("""
        SELECT COUNT(x_coordinate) FROM cricket.cricsheet_deliveries
    """)
    res2 = cur.fetchone()
    print(f"Cricsheet deliveries with coords: {res2[0]}")
except Exception as e:
    print(f"Cricsheet coords check failed: {e}")
    
conn.rollback()

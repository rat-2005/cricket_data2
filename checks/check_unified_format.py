from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT format FROM cricket.unified_deliveries")
        print(cur.fetchall())

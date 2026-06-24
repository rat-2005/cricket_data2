from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT tournament FROM cricket.unified_deliveries")
        for r in cur.fetchall():
            print(r[0])

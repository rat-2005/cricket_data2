from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN zad IS NULL THEN 1 ELSE 0 END) FROM cricket.unified_deliveries")
        row = cur.fetchone()
        print("Total unified_deliveries:", row[0])
        print("Deliveries with NULL zad:", row[1])

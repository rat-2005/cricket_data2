from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'cricket' AND table_name = 'unified_deliveries'")
        for r in cur.fetchall():
            print(r)

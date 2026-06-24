from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        print("Creating index...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_unified_tournaments ON cricket.unified_deliveries (tournament, match_date)")
        conn.commit()
        print("Done!")

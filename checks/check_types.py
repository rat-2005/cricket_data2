from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cricsheet_matches'")
        print("cricsheet_matches:", cur.fetchall())
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'unified_deliveries'")
        print("unified_deliveries:", cur.fetchall())

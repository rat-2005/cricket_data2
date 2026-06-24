from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cricsheet_matches'")
        for r in cur.fetchall():
            print(r[0])

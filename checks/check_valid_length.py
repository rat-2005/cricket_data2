from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ball_line_length FROM cricket.unified_deliveries WHERE ball_line_length NOT LIKE '%,%' LIMIT 20")
        print([r[0] for r in cur.fetchall()])

from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ball_line_length FROM cricket.unified_deliveries LIMIT 20")
        print("ball_line_length:", [r[0] for r in cur.fetchall()])

from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cricket.cricsheet_deliveries WHERE batsman_id = '253802'")
        print("Total cricsheet balls for Kohli globally:", cur.fetchone()[0])

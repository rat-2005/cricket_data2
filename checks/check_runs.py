from app import get_db_connection

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT SUM(batsman_runs) 
            FROM cricket.unified_deliveries 
            WHERE batsman_name LIKE '%Kohli%' AND tournament LIKE 'ICC Men''s T20 World Cup%'
        """)
        print("Runs in all T20 World Cups:", cur.fetchone()[0])

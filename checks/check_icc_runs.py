from app import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT batsman_runs FROM cricket.unified_deliveries WHERE source_database = 'ICC' LIMIT 10
    """)
    res = cur.fetchall()
    print(res)

from app import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT source_database, COUNT(*) as total, COUNT(batsman_runs) as has_runs
        FROM cricket.unified_deliveries 
        GROUP BY source_database
    """)
    for r in cur.fetchall():
        print(r)

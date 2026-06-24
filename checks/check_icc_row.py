from app import get_db_connection

with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM cricket.unified_deliveries 
        WHERE source_database = 'ICC' 
          AND match_date::date = '2022-11-02'
          AND bowler_name = 'Taskin Ahmed'
        LIMIT 1
    """)
    res = cur.fetchone()
    if res:
        cols = [d[0] for d in cur.description]
        print(dict(zip(cols, res)))

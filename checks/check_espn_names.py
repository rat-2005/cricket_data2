from app import get_db_connection

def check_espn_names():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT batsman_name
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN'
              AND match_date::date = '2022-11-02'
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    check_espn_names()

from app import get_db_connection

def check_espn_dates():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT match_date, COUNT(*)
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN'
              AND batsman_id = '253802'
              AND match_date >= '2022-10-30'
              AND match_date <= '2022-11-05'
            GROUP BY match_date
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    check_espn_dates()

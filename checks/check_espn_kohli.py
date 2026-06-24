from app import get_db_connection

def check_espn_kohli():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT over_number, ball_in_over, batsman_runs, overs_actual, innings
            FROM cricket.unified_deliveries 
            WHERE source_database = 'ESPN'
              AND match_date::date = '2022-11-02'
              AND batsman_id = '253802'
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    check_espn_kohli()

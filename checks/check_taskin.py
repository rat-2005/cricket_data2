from app import get_db_connection

def check_taskin_six():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT over_number, ball_in_over, batsman_runs, bowler_name, zad
            FROM cricket.unified_deliveries 
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli') 
              AND match_date::date = '2022-11-02'
              AND bowler_name = 'Taskin Ahmed'
            ORDER BY over_number, ball_in_over
        """)
        res = cur.fetchall()
        for r in res:
            print(r)

if __name__ == '__main__':
    check_taskin_six()

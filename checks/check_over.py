from app import get_db_connection

def check_over():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT over_number, ball_in_over, overs_actual 
            FROM cricket.unified_deliveries 
            WHERE match_date::date = '2022-11-10' 
              AND bowler_name ILIKE '%Woakes%' 
              AND batsman_name ILIKE '%Kohli%'
              AND source_database = 'ICC'
            ORDER BY ball_in_over
        """)
        for row in cur.fetchall():
            print(row)

if __name__ == '__main__':
    check_over()

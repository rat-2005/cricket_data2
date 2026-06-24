from app import get_db_connection

def test_join():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Look at both ICC and Cricsheet data for Kohli vs Bangladesh
        cur.execute("""
            SELECT source_database, over_number, ball_in_over, batsman_runs, bowler_name, zad
            FROM cricket.unified_deliveries 
            WHERE batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli') 
              AND match_date::date = '2022-11-02'
              AND bowler_name = 'Taskin Ahmed'
            ORDER BY source_database, over_number, ball_in_over
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    test_join()

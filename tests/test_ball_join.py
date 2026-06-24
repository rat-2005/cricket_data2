from app import get_db_connection

def test_ball_join():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT i.over_number, i.ball_in_over as icc_ball, e.ball_in_over as espn_ball, e.batsman_runs
            FROM cricket.unified_deliveries i
            LEFT JOIN cricket.unified_deliveries e
              ON i.match_date = e.match_date
             AND i.over_number = e.over_number
             AND i.ball_in_over = e.ball_in_over
             AND e.source_database = 'ESPN'
            WHERE i.source_database = 'ICC'
              AND i.match_date::date = '2022-11-02'
              AND i.batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
            ORDER BY i.over_number, i.ball_in_over
            LIMIT 20
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    test_ball_join()

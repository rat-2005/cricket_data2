from app import get_db_connection

def test_join_logic():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT i.over_number, i.ball_in_over, i.bowler_name, i.zad, e.batsman_runs
            FROM cricket.unified_deliveries i
            LEFT JOIN cricket.unified_deliveries e
              ON i.match_date = e.match_date
             AND i.batsman_name = e.batsman_name
             AND i.bowler_name = e.bowler_name
             AND i.over_number = e.over_number
             AND e.source_database = 'ESPN'
            WHERE i.source_database = 'ICC'
              AND i.match_date::date = '2022-11-02'
              AND i.batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
              AND i.zad IS NOT NULL AND i.zad != ''
            ORDER BY i.over_number, i.ball_in_over
        """)
        res = cur.fetchall()
        for r in res:
            print(r)

if __name__ == '__main__':
    test_join_logic()

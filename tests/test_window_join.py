from app import get_db_connection

def test_window_join():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            WITH icc AS (
                SELECT match_date, over_number, ball_in_over, bowler_name, zad,
                       ROW_NUMBER() OVER(PARTITION BY match_date, innings, over_number ORDER BY ball_in_over) as ball_idx
                FROM cricket.unified_deliveries
                WHERE source_database = 'ICC'
                  AND match_date::date = '2022-11-02'
                  AND batsman_name IN ('Virat Kohli', 'V Kohli', 'V. Kohli')
            ),
            espn AS (
                SELECT match_date, over_number - 1 AS over_number, ball_in_over, batsman_runs,
                       ROW_NUMBER() OVER(PARTITION BY match_date, innings, over_number ORDER BY overs_actual) as ball_idx
                FROM cricket.unified_deliveries
                WHERE source_database = 'ESPN'
                  AND match_date::date = '2022-11-02'
                  AND batsman_id = '253802' -- Virat Kohli ESPN ID
            )
            SELECT i.over_number, i.ball_idx, i.zad, e.batsman_runs
            FROM icc i
            LEFT JOIN espn e
              ON i.match_date::date = e.match_date::date
             AND i.over_number = e.over_number
             AND i.ball_idx = e.ball_idx
            ORDER BY i.over_number, i.ball_idx
            LIMIT 20
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    test_window_join()

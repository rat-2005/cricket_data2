import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                    SELECT 
                        u.zad, 
                        u.batsman_runs, 
                        u.over_number, 
                        u.ball_in_over, 
                        u.bowler_name,
                        u.shot_type,
                        u.match_date,
                        (
                            SELECT d.ball_number 
                            FROM cricket.cricsheet_deliveries d
                            JOIN cricket.cricsheet_matches m ON m.id = d.match_id
                            WHERE d.batsman_id = '253802'
                              AND d.over_number = u.over_number
                              AND m.match_date = u.match_date
                              AND d.batsman_runs = CASE 
                                WHEN CAST(split_part(u.zad, ',', 2) AS INTEGER) >= 6 THEN 6
                                WHEN CAST(split_part(u.zad, ',', 2) AS INTEGER) = 5 THEN 4
                                WHEN CAST(split_part(u.zad, ',', 2) AS INTEGER) >= 2 THEN 1
                                ELSE 0 END
                            LIMIT 1
                        ) as fallback_ball
                    FROM cricket.unified_deliveries u
                    WHERE u.batsman_name IN ('Virat Kohli') 
                      AND u.bowler_name IN ('Naveen-ul-Haq Murid') 
                      AND u.source_database = 'ICC'
                    ORDER BY u.match_date DESC
                    LIMIT 500
            """)
            rows = cur.fetchall()
            print(f"Returned rows: {len(rows)}")
            for r in rows:
                print(r)
        except Exception as e:
            print("Error:", e)

if __name__ == '__main__':
    test()

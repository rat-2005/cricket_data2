import psycopg2
from app import get_db_connection

def test_crash():
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT 
                    u.zad,
                    (
                        SELECT d.ball_number 
                        FROM cricket.cricsheet_deliveries d
                        JOIN cricket.cricsheet_matches m ON m.id = d.match_id
                        WHERE d.batsman_id = '253802'
                          AND d.over_number = u.over_number
                          AND m.match_date = u.match_date
                          AND d.batsman_runs = CASE 
                            WHEN CAST(split_part(u.zad, ',', 2) AS INTEGER) >= 6 THEN 6
                            ELSE 0 END
                        LIMIT 1
                    ) as fallback_ball
                FROM cricket.unified_deliveries u
                WHERE u.batsman_name = 'Virat Kohli'
                  AND u.bowler_name ILIKE '%Naveen%'
                  AND u.source_database = 'ICC'
            """)
            print("Query succeeded!")
        except Exception as e:
            print("Query failed:", e)

if __name__ == '__main__':
    test_crash()

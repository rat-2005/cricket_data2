import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def get_ball_data():
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT match_date, over_number, ball_in_over, batsman_runs, angle, distance
            FROM cricket.unified_deliveries
            WHERE batsman_name = 'Virat Kohli'
              AND bowler_name ILIKE '%Haris Rauf%'
              AND source_database = 'ICC'
            ORDER BY match_date DESC
            LIMIT 20
        """)
        for row in cur.fetchall():
            print(f"Date {row['match_date']}, Over {row['over_number']}, Ball {row['ball_in_over']}: {row['batsman_runs']} runs. Coordinates: angle={row.get('angle')}, distance={row.get('distance')}")

if __name__ == '__main__':
    get_ball_data()

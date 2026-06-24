import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def get_ball_data():
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT over_number, ball_in_over, batsman_runs, bowler_name, x_coordinate, y_coordinate, zad, text, short_text
            FROM cricket.unified_deliveries
            WHERE match_date::date = '2022-10-23'
              AND batsman_name = 'Virat Kohli'
              AND bowler_name ILIKE '%Haris Rauf%'
              AND source_database = 'ICC'
            ORDER BY over_number DESC, ball_in_over DESC
        """)
        for row in cur.fetchall():
            print(f"Over {row['over_number']} Ball {row['ball_in_over']}: zad={row.get('zad')}, x={row.get('x_coordinate')}, y={row.get('y_coordinate')}")

if __name__ == '__main__':
    get_ball_data()

import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def test_faceoff_wagon():
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Kohli vs Naveen-ul-Haq Murid
        cur.execute("""
            SELECT u.match_date, u.batsman_runs, u.zad
            FROM cricket.unified_deliveries u
            WHERE batsman_name = 'Virat Kohli'
              AND bowler_name ILIKE '%Naveen%'
              AND source_database = 'ICC'
        """)
        rows = cur.fetchall()
        print(f"ICC deliveries found for Kohli vs Naveen: {len(rows)}")
        for r in rows:
            print(r)

if __name__ == '__main__':
    test_faceoff_wagon()

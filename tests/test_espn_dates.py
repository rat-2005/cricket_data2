import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.date, c.description 
            FROM cricket.deliveries d 
            JOIN cricket.competitions c ON c.id=d.competition_id 
            WHERE d.batsman_id = '253802' AND d.bowler_id = '311592'
            AND c.date IN (
                SELECT DISTINCT match_date::date 
                FROM cricket.unified_deliveries 
                WHERE tournament LIKE 'ICC Cricket World Cup, 2023%'
            )
        """)
        print(cur.fetchall())

if __name__ == '__main__':
    test()

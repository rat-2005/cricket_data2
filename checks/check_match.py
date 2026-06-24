from app import get_db_connection

def check_match():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT tournament, match_date, bowler_name, batsman_name 
            FROM cricket.unified_deliveries 
            WHERE match_date::date = '2022-11-10' 
              AND bowler_name ILIKE '%Woakes%' 
              AND source_database = 'ICC' 
            LIMIT 1
        """)
        print(cur.fetchone())

if __name__ == '__main__':
    check_match()

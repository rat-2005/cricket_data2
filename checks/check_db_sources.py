from app import get_db_connection

def check_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT source_database, COUNT(*)
            FROM cricket.unified_deliveries 
            WHERE match_date::date = '2022-11-02'
            GROUP BY source_database
        """)
        print("For match_date = 2022-11-02:")
        for r in cur.fetchall():
            print(r)
            
        cur.execute("""
            SELECT source_database, COUNT(*)
            FROM cricket.unified_deliveries 
            GROUP BY source_database
        """)
        print("\nAll data:")
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    check_db()

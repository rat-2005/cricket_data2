from app import get_db_connection

def check_kohli_id():
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, full_name
            FROM cricket.athletes 
            WHERE full_name ILIKE '%Kohli%'
        """)
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    check_kohli_id()

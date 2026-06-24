from app import get_db_connection

def check_columns():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='unified_deliveries'")
        for r in cur.fetchall():
            print(r[0])

if __name__ == '__main__':
    check_columns()

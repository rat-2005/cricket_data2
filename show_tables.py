from app import get_db_connection

def show_tables():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'cricket'")
        for r in cur.fetchall():
            print(r)

if __name__ == '__main__':
    show_tables()

import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT tournament FROM cricket.unified_deliveries WHERE tournament ILIKE '%World Cup%'")
        print(cur.fetchall())

if __name__ == '__main__':
    test()

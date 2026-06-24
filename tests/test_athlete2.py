import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, full_name, short_name FROM cricket.athletes WHERE id IN ('253802', '34102', '28081', '219889')")
        print(cur.fetchall())

if __name__ == '__main__':
    test()

import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, full_name FROM cricket.athletes WHERE full_name ILIKE '%Naveen%'")
        print(cur.fetchall())

if __name__ == '__main__':
    test()

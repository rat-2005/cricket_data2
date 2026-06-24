import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT full_name, first_name, last_name, playing_name FROM cricket.athletes WHERE id = '793447'")
        print(cur.fetchall())

if __name__ == '__main__':
    test()

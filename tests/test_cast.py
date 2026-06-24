import psycopg2
from app import get_db_connection

def test_cast():
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT CAST('' AS INTEGER)")
            print(cur.fetchall())
        except Exception as e:
            print("Error:", e)

if __name__ == '__main__':
    test_cast()

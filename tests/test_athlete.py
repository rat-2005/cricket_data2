import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cricket.athletes WHERE id = '34102'")
        print([desc[0] for desc in cur.description])
        print(cur.fetchone())

if __name__ == '__main__':
    test()

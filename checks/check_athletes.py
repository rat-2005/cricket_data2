from app import get_db_connection

def check_athletes():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cricket.athletes LIMIT 1")
        res = cur.fetchone()
        if res:
            cols = [d[0] for d in cur.description]
            print(dict(zip(cols, res)))

if __name__ == '__main__':
    check_athletes()

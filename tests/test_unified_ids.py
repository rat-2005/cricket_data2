import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT batsman_id, batsman_name FROM cricket.unified_deliveries WHERE batsman_name IN ('Rohit Sharma', 'David Warner', 'Virat Kohli') LIMIT 10")
        print(cur.fetchall())
        
if __name__ == '__main__':
    test()

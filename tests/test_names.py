import psycopg2
from app import get_db_connection

def test():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT batsman_name FROM cricket.unified_deliveries WHERE source_database = 'ICC' LIMIT 20")
        print(cur.fetchall())
        
        cur.execute("SELECT full_name FROM cricket.athletes WHERE id IN ('253802', '34102', '28081', '219889')")
        print(cur.fetchall())

if __name__ == '__main__':
    test()

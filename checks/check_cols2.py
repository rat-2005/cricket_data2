import psycopg2
from app import get_db_connection

def find_cricsheet_matches():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cricsheet_deliveries'
        """)
        print("Cricsheet deliveries columns:", [row[0] for row in cur.fetchall()])

if __name__ == '__main__':
    find_cricsheet_matches()

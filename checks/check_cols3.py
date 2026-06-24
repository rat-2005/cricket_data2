import psycopg2
from app import get_db_connection

def get_columns():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='unified_deliveries'
        """)
        print("Columns:", [row[0] for row in cur.fetchall()])

if __name__ == '__main__':
    get_columns()

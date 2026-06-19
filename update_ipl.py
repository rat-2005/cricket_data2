import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def update_ipl():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("""
        UPDATE cricket.competitions 
        SET class_name = 'IPL' 
        WHERE event_id IN (
            SELECT event_id FROM cricket.event_leagues WHERE league_id = '8048'
        )
    """)
    conn.commit()
    print('Updated', cur.rowcount, 'rows to IPL class')

if __name__ == '__main__':
    update_ipl()

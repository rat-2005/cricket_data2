import os
import psycopg2
from dotenv import load_dotenv

def clear_database():
    load_dotenv()
    
    # Try using DATABASE_URL first
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        print("Connecting using DATABASE_URL...")
        conn = psycopg2.connect(db_url)
    else:
        print("Connecting using individual DB credentials...")
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
    
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("WARNING: Wiping all data from the cricket schema...")
    
    try:
        # Using CASCADE on the top-level tables will automatically delete all child rows 
        # (competitions, deliveries, dismissals, innings, etc) instantly.
        cursor.execute("""
            TRUNCATE TABLE 
                cricket.venues, 
                cricket.teams, 
                cricket.athletes, 
                cricket.leagues, 
                cricket.events 
            CASCADE;
        """)
        print("✅ Database successfully cleared! All 18 tables are now empty.")
        
        # Also clear the progress tracker so ingest_bulk.py re-processes everything
        progress_file = os.path.join(os.path.dirname(__file__), 'completed_events.txt')
        open(progress_file, 'w').close()
        print("✅ completed_events.txt cleared.")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL data? (y/n): ")
    if confirm.lower() == 'y':
        clear_database()
    else:
        print("Operation cancelled.")

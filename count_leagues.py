import psycopg2
import os
from dotenv import load_dotenv

def count_leagues():
    # Load database URL from .env file
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("Error: DATABASE_URL not found in environment variables.")
        return

    try:
        # Connect to your PostgreSQL database
        print("Connecting to the database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Count unique leagues
        cur.execute("SELECT COUNT(*) FROM cricket.leagues;")
        unique_leagues = cur.fetchone()[0]
        
        # Count event-to-league mappings
        cur.execute("SELECT COUNT(*) FROM cricket.event_leagues;")
        event_league_mappings = cur.fetchone()[0]
        
        print("-" * 50)
        print("LEAGUE COUNTS IN DATABASE")
        print("-" * 50)
        print(f"Total Unique Leagues:         {unique_leagues:,}")
        print(f"Total Event-League Mappings:  {event_league_mappings:,}")
        print("-" * 50)
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    count_leagues()

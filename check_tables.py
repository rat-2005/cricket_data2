import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        return

    try:
        # Connect to the database
        print("Connecting to the database...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get all tables in the 'cricket' schema dynamically
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'cricket' 
            ORDER BY table_name;
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        print(f"Found {len(tables)} tables in the 'cricket' schema.\n")

        # Query and print row counts for each table
        print(f"{'Table Name'.ljust(35)} | Row Count")
        print("-" * 55)
        
        total_rows = 0
        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM cricket.{table};")
            count = cur.fetchone()['count']
            total_rows += count
            print(f"cricket.{table.ljust(27)} | {count:,}")
            
        print("-" * 55)
        print(f"{'TOTAL'.ljust(35)} | {total_rows:,}\n")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()

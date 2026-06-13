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

        # Query and print 100 rows for each table
        for table in tables:
            print(f"{'='*80}")
            print(f"TABLE: cricket.{table} (LIMIT 100)")
            print(f"{'='*80}")
            
            cur.execute(f"SELECT * FROM cricket.{table} LIMIT 100;")
            rows = cur.fetchall()
            
            if not rows:
                print("(Table is empty)\n")
                continue
                
            # Print column headers (truncated to 20 chars for formatting)
            columns = list(rows[0].keys())
            header = " | ".join(str(col).ljust(20)[:20] for col in columns)
            print(header)
            print("-" * len(header))
            
            # Print rows (truncated to 20 chars for formatting)
            for row in rows:
                row_str = " | ".join(str(row[col]).replace('\n', ' ').ljust(20)[:20] for col in columns)
                print(row_str)
                
            print(f"\n[ Fetched {len(rows)} rows from cricket.{table} ]\n")

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()

import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
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
    
    print("Reading schema.sql...")
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    print("Executing schema.sql...")
    try:
        cursor.execute(schema_sql)
        print("Schema successfully executed! All 18 tables created.")
    except Exception as e:
        print(f"Error executing schema: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_database()

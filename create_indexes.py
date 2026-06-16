import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

try:
    print("Building indexes on deliveries for faster joins...")
    
    # Drop existing indexes if they exist  
    cur.execute("DROP INDEX IF EXISTS idx_deliveries_batsman_id")
    cur.execute("DROP INDEX IF EXISTS idx_deliveries_bowler_id")
    cur.execute("DROP INDEX IF EXISTS idx_deliveries_batting_team")
    cur.execute("DROP INDEX IF EXISTS idx_deliveries_bowling_team")
    conn.commit()
    
    print("  Creating index on batsman_id...")
    cur.execute("CREATE INDEX idx_deliveries_batsman_id ON cricket.deliveries(batsman_id)")
    conn.commit()
    
    print("  Creating index on bowler_id...")
    cur.execute("CREATE INDEX idx_deliveries_bowler_id ON cricket.deliveries(bowler_id)")
    conn.commit()
    
    print("  Creating index on batting_team_id...")
    cur.execute("CREATE INDEX idx_deliveries_batting_team ON cricket.deliveries(batting_team_id)")
    conn.commit()
    
    print("  Creating index on bowling_team_id...")
    cur.execute("CREATE INDEX idx_deliveries_bowling_team ON cricket.deliveries(bowling_team_id)")
    conn.commit()
    
    print("\n✅ Indexes created!")
    print("\nNow run rebuild_fast_indexed.py to perform the rebuild with proper indexes...")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

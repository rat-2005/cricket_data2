import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
cur = conn.cursor()

try:
    print("Forcing drop of old bowler_stats_mv...")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS cricket.bowler_stats_mv CASCADE")
    print("✅ Dropped")
    
    print("Creating new bowler_stats_mv from deliveries...")
    cur.execute("""
        CREATE MATERIALIZED VIEW cricket.bowler_stats_mv AS
        SELECT 
            d.bowler_id::VARCHAR as athlete_id,
            c.class_name as format,
            COUNT(*)::INT as deliveries_bowled
        FROM cricket.deliveries d
        JOIN cricket.competitions c ON d.competition_id::text = c.id::text
        WHERE d.bowler_id IS NOT NULL
        GROUP BY d.bowler_id, c.class_name
    """)
    print("✅ Materialized view created!")
    
    print("\nVerifying data - Top ODI bowlers...")
    cur.execute("""
        SELECT athlete_id, deliveries_bowled 
        FROM cricket.bowler_stats_mv 
        WHERE format = 'ODI'
        ORDER BY deliveries_bowled DESC 
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} deliveries")
    
    print("\n✅ Complete! Both MVs are now pulling from deliveries with complete data")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()

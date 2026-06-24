import psycopg2
from psycopg2.extras import RealDictCursor
from app import get_db_connection

def find_missing_mappings():
    print("Connecting to database...")
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Get all distinct batsman names from ICC data
        cur.execute("""
            SELECT DISTINCT batsman_name
            FROM cricket.unified_deliveries
            WHERE source_database = 'ICC'
        """)
        icc_names = [row[0] for row in cur.fetchall()]
        print(f"Found {len(icc_names)} unique ICC batsmen.")
        
        # Try to map them
        mapped_count = 0
        unmapped = []
        for name in icc_names:
            cur.execute("""
                SELECT id, full_name FROM cricket.athletes 
                WHERE full_name = %s OR full_name ILIKE %s
                LIMIT 1
            """, (name, f"%{name}%"))
            res = cur.fetchone()
            if res:
                mapped_count += 1
            else:
                unmapped.append(name)
                
        print(f"Mapped {mapped_count}/{len(icc_names)} batsmen.")
        if unmapped:
            print("Unmapped:", unmapped[:20])

if __name__ == '__main__':
    find_missing_mappings()

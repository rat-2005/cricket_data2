import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    try:
        load_dotenv()
        db_url = os.getenv('DATABASE_URL')
        print(f"Connecting to database...")
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=5.0)
        print("Connected!")
        
        # Quick check
        res = await conn.fetchval("SELECT COUNT(*) FROM cricket.deliveries")
        print(f"Deliveries table has {res:,} rows")
        
        # Check what indexes exist
        res2 = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'deliveries' AND schemaname = 'cricket'
        """)
        print(f"\nIndexes on deliveries table:")
        for idx in res2:
            print(f"  - {idx['indexname']}")
        
        await conn.close()
    except asyncio.TimeoutError:
        print("Connection timeout")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(run())

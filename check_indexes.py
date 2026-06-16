import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('=== Checking indexes on deliveries table ===\n')
    
    res = await conn.fetch("""
        SELECT
            t.relname as table_name,
            i.relname as index_name,
            a.attname as column_name
        FROM
            pg_class t
            JOIN pg_index idx ON t.oid = idx.indrelid
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
        WHERE
            t.relname = 'deliveries'
        ORDER BY i.relname, a.attnum;
    """)
    
    if res:
        for row in res:
            print(f"Index: {row['index_name']}, Column: {row['column_name']}")
    else:
        print("No indexes found!")
    
    print('\n=== Checking table size ===\n')
    res2 = await conn.fetch("""
        SELECT 
            pg_size_pretty(pg_total_relation_size('cricket.deliveries')) as table_size,
            COUNT(*) as row_count
        FROM cricket.deliveries
    """)
    print(dict(res2[0]))
    
    await conn.close()

asyncio.run(run())

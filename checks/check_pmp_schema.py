import os, asyncio, asyncpg
from dotenv import load_dotenv

async def run():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print("=== Player Match Performances Table Structure ===\n")
    
    res = await conn.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'cricket' AND table_name = 'player_match_performances'
        ORDER BY ordinal_position
    """)
    
    for col in res:
        print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    await conn.close()

asyncio.run(run())

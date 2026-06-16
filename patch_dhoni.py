import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.environ.get('DATABASE_URL'))
    
    query = """
    UPDATE cricket.deliveries 
    SET is_leg_bye = FALSE, batsman_runs = 1 
    WHERE batsman_id = '28081' 
      AND over_number = 14 
      AND ball_in_over = 4 
      AND competition_id IN (
          SELECT id FROM cricket.events WHERE CAST(date AS DATE) = '2012-04-12'
      )
    """
    res = await conn.execute(query)
    print("Database Patch Result:", res)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())

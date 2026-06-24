import asyncio
import asyncpg
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def check_connection():
    # Load environment variables from .env file
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logging.error("DATABASE_URL not found in environment variables.")
        return

    logging.info(f"Attempting to connect to the database...")
    
    try:
        # Try to establish a connection
        conn = await asyncpg.connect(db_url)
        
        # If successful, execute a simple query to get the PostgreSQL version
        version = await conn.fetchval('SELECT version();')
        
        logging.info("✅ Connection successful!")
        logging.info(f"Database Version: {version}")
        
        # Close the connection
        await conn.close()
        
    except asyncpg.exceptions.InvalidPasswordError:
        logging.error("❌ Authentication failed: Invalid password.")
    except Exception as e:
        logging.error(f"❌ Connection failed. Error: {e}")
        logging.warning("If this is a timeout error, it likely means your IP address is not allowed by the RDS Security Group, or Public Access is disabled.")

if __name__ == '__main__':
    asyncio.run(check_connection())

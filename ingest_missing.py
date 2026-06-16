import asyncio
import os
import json
import logging
import re
import asyncpg
import aiohttp
from dotenv import load_dotenv

# Import functions from ingest_upsert.py without running its main block
from ingest_upsert import process_match, cached_athletes, cached_teams, cached_venues, progress, cache_lock

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

async def worker(pool, session, queue, worker_id):
    while True:
        try:
            event_url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        try:
            await asyncio.wait_for(
                process_match(pool, session, event_url),
                timeout=300
            )
            progress['done'] += 1
            log.info(f"[W{worker_id:02d}] ✓ {progress['done']}/{progress['total']} processed. URL: {event_url}")
        except asyncio.TimeoutError:
            log.warning(f"[W{worker_id:02d}] ⏰ TIMEOUT - skipped: {event_url}")
        except Exception as e:
            log.error(f"[W{worker_id:02d}] ✗ {event_url}: {e}")
        finally:
            queue.task_done()

async def ingest_missing():
    load_dotenv()
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    with open('events.json', 'r') as f:
        urls = json.load(f)
    
    # Pre-filter JSON IDs
    json_url_map = {}
    for u in urls:
        m = re.search(r'/events/(\d+)', u)
        if m:
            json_url_map[m.group(1)] = u
    
    pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    async with pool.acquire() as conn:
        records = await conn.fetch("SELECT id FROM cricket.events")
        db_ids = {str(r['id']) for r in records}
        
    missing_ids = set(json_url_map.keys()) - db_ids
    missing_urls = [json_url_map[mid] for mid in missing_ids]
    
    if not missing_urls:
        log.info("No missing matches found! All 104,242 present.")
        await pool.close()
        return
        
    log.info(f"Found {len(missing_urls)} missing matches. Pre-warming caches...")
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM cricket.athletes")
        cached_athletes.update(r['id'] for r in rows)
        rows = await conn.fetch("SELECT id FROM cricket.teams")
        cached_teams.update(r['id'] for r in rows)
        rows = await conn.fetch("SELECT id FROM cricket.venues")
        cached_venues.update(r['id'] for r in rows)
        
    queue = asyncio.Queue()
    for url in missing_urls:
        queue.put_nowait(url)
        
    progress['total'] = queue.qsize()
    progress['done'] = 0
    
    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300, enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [asyncio.create_task(worker(pool, session, queue, i)) for i in range(5)]
        await queue.join()
        for w in workers: w.cancel()
        
    await pool.close()
    log.info("Missing match ingestion complete!")

if __name__ == '__main__':
    asyncio.run(ingest_missing())

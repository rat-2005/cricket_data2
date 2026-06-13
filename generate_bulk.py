import os

with open('ingest_sample.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_main = False
in_helpers = False
for line in lines:
    if line.startswith('async def ingest_sample():'):
        in_main = True
        new_lines.append('async def process_match(pool, session, event_url, progress_file):\n')
        new_lines.append('    EVENT_URL = event_url\n')
        continue
    
    if in_main:
        if line.strip() == "EVENT_URL = \"http://core.espnuk.org/v2/sports/cricket/leagues/8039/events/1336043\"":
            continue
        if line.strip() == 'db_url = os.getenv("DATABASE_URL")':
            continue
        if line.strip() == 'pool = await asyncpg.create_pool(db_url)':
            continue
        if line.strip() == 'async with aiohttp.ClientSession() as session:':
            continue
        if line.strip() == 'log.info("=" * 60)':
            break # stop at the final report

        # unindent 8 spaces since we removed the async with session
        if line.startswith('        '):
            new_lines.append(line[8:])
        elif line == '\n':
            new_lines.append(line)
        else:
            new_lines.append(line)
    elif line.startswith('SEM = asyncio.Semaphore(30)'):
        continue # remove global semaphore
    elif line.startswith('async def fetch(session, url'):
        new_lines.append('async def fetch(session, url, retries=3):\n')
        new_lines.append('    if not url: return None\n')
        new_lines.append('    for attempt in range(retries):\n')
        new_lines.append('        try:\n')
        new_lines.append('            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:\n')
        new_lines.append('                if resp.status == 200:\n')
        new_lines.append('                    return await resp.json()\n')
        new_lines.append('                elif resp.status in (429, 502, 503, 504):\n')
        new_lines.append('                    await asyncio.sleep(2 ** attempt)\n')
        new_lines.append('                    continue\n')
        new_lines.append('        except Exception as e:\n')
        new_lines.append('            if attempt == retries - 1:\n')
        new_lines.append('                log.warning(f"Fetch failed: {url} -> {e}")\n')
        new_lines.append('            await asyncio.sleep(2 ** attempt)\n')
        new_lines.append('    return None\n')
    elif 'async with SEM:' in line or 'if resp.status == 200:' in line or 'return await resp.json()' in line or 'except Exception as e:' in line or 'log.warning(f"Fetch failed:' in line or 'return None' in line:
        pass # removed old fetch body
    else:
        new_lines.append(line)

queue_worker_code = """
    # Write to progress file when done
    progress_file.write(event_url + '\\n')
    progress_file.flush()

async def worker(pool, session, queue, progress_file, worker_id):
    while True:
        try:
            event_url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        try:
            log.info(f"[Worker {worker_id}] Processing {event_url}")
            await process_match(pool, session, event_url, progress_file)
        except Exception as e:
            log.error(f"[Worker {worker_id}] Error processing {event_url}: {e}")
        finally:
            queue.task_done()

async def main():
    import json
    
    # Load all events
    try:
        with open('events.json', 'r', encoding='utf-8') as f:
            all_events = json.load(f)
    except FileNotFoundError:
        log.error("events.json not found! Cannot bulk ingest.")
        return
        
    # Load progress
    completed_events = set()
    try:
        with open('completed_events.txt', 'r', encoding='utf-8') as f:
            completed_events = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        pass
        
    queue = asyncio.Queue()
    for event_url in all_events:
        if event_url not in completed_events:
            queue.put_nowait(event_url)
            
    log.info(f"Total events: {len(all_events)}")
    log.info(f"Completed events: {len(completed_events)}")
    log.info(f"Events to process: {queue.qsize()}")
    
    if queue.qsize() == 0:
        log.info("All events processed!")
        return

    db_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(db_url, min_size=10, max_size=50)
    
    progress_file = open('completed_events.txt', 'a', encoding='utf-8')
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [asyncio.create_task(worker(pool, session, queue, progress_file, i)) for i in range(50)]
        await asyncio.gather(*workers)
        
    progress_file.close()
    await pool.close()
    log.info("Bulk ingestion complete!")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
"""

# write new lines
with open('ingest_bulk.py', 'w', encoding='utf-8') as f:
    for line in new_lines:
        if "if __name__ == '__main__':" in line:
            break
        f.write(line)
    f.write(queue_worker_code)

print("ingest_bulk.py generated successfully.")

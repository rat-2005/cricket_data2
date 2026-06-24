import aiohttp
import asyncio
import time

# A lightweight endpoint to test against (a specific match page)
TEST_URL = "http://core.espnuk.org/v2/sports/cricket/leagues/1154639/events/1154659"

async def fetch_test(session, url):
    start = time.time()
    try:
        async with session.get(url, timeout=5) as resp:
            # We don't even need to parse the JSON, just checking the status code triggers the limit
            await resp.read() 
            return resp.status, time.time() - start
    except Exception as e:
        return 999, time.time() - start # 999 represents a connection error or timeout

async def run_batch(batch_size):
    print(f"Testing {batch_size} concurrent requests...")
    
    connector = aiohttp.TCPConnector(limit=batch_size)
    async with aiohttp.ClientSession(connector=connector) as session:
        start_time = time.time()
        
        # Fire all requests at the exact same moment
        tasks = [fetch_test(session, TEST_URL) for _ in range(batch_size)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Tally results
        status_counts = {}
        for status, _ in results:
            status_counts[status] = status_counts.get(status, 0) + 1
            
        successes = status_counts.get(200, 0)
        throttles = status_counts.get(429, 0)
        errors = sum(v for k, v in status_counts.items() if k not in (200, 429))
        
        print(f"  Results in {elapsed:.2f}s: {successes} Success (200), {throttles} Throttled (429), {errors} Errors")
        
        return throttles > 0

async def main():
    print(f"--- ESPN API Rate Limit Tester ---")
    print(f"Target: {TEST_URL}\n")
    
    # Ramp up concurrency levels to find the exact breaking point
    levels = [10, 25, 40, 50, 75, 100, 125, 150, 200, 250, 300]
    
    for level in levels:
        hit_limit = await run_batch(level)
        
        if hit_limit:
            print(f"\n⚠️ RATE LIMIT HIT AT {level} CONCURRENT REQUESTS!")
            print(f"ESPN's strict threshold is roughly {level} requests per second.")
            print("This is exactly why the main script pauses when we set the semaphore to 250.")
            break
            
        # Cool down before the next burst so we don't trigger limits prematurely
        print("  Cooling down for 3 seconds...")
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())

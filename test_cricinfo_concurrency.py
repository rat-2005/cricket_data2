import asyncio
import time
import hmac
import hashlib
from curl_cffi import requests

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
BASE_URL = "https://hs-consumer-api.cricinfo.com"

# Example match and series ID to test against
SERIES_ID = "1387592"
MATCH_ID = "1387599"

def get_auth_token(path):
    t = f"exp={int(time.time()) + 60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

async def make_request(session, req_id):
    path = f"/v1/pages/match/home?lang=en&seriesId={SERIES_ID}&matchId={MATCH_ID}"
    headers = {
        "x-hsci-auth-token": get_auth_token(path),
        "Origin": "https://www.espncricinfo.com",
        "Referer": "https://www.espncricinfo.com/",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    start = time.time()
    try:
        r = await session.get(f"{BASE_URL}{path}", headers=headers, timeout=10)
        return r.status_code, time.time() - start
    except Exception as e:
        return str(e), time.time() - start

async def test_batch(concurrency_level):
    print(f"\n[{concurrency_level} Concurrent Connections]")
    print(f"Firing {concurrency_level} parallel requests to Akamai/ESPN...")
    
    async with requests.AsyncSession(impersonate="chrome") as session:
        tasks = []
        for i in range(concurrency_level):
            tasks.append(make_request(session, i))
            
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        status_counts = {}
        for status, latency in results:
            status_counts[status] = status_counts.get(status, 0) + 1
            
        print(f"Batch completed in {total_time:.2f} seconds.")
        print("Results:")
        for status, count in status_counts.items():
            print(f"  HTTP {status}: {count} responses")
            
        # Check if we triggered any 403 or 429
        if status_counts.get(200, 0) == concurrency_level:
            print("  [OK] 100% SUCCESS RATE")
            return True
        else:
            print("  [ERROR] ERRORS DETECTED (Rate limit or Akamai block)")
            return False

async def main():
    print("=== Cricinfo Akamai Load Test ===")
    print("Testing maximum concurrent connection limits using curl_cffi impersonation.")
    
    levels = [10, 50, 100, 250, 500, 600,700,800,950]
    
    for level in levels:
        success = await test_batch(level)
        if not success:
            print("\n[!] Limit reached! The connection method maxes out around this concurrency.")
            break
        await asyncio.sleep(2) # Brief cooldown between batches

if __name__ == "__main__":
    asyncio.run(main())

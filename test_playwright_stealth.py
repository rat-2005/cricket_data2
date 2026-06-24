import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth(page)
        
        print("Loading main site to bypass Akamai with Stealth...")
        try:
            await page.goto('https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-1st-t20i-1387597/live-cricket-score', wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(3000) 
        except Exception as e:
            print("Timeout or error loading main site:", e)
            
        print("Cookies captured:")
        cookies = await context.cookies()
        for c in cookies:
            if c['name'] in ('_abck', 'bm_sz'):
                print(c['name'], '->', c['value'][:20] + '...')
                
        # Try fetching the API directly using the page context
        api_url = 'https://hs-consumer-api.cricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387597&sortDirection=DESC'
        
        print("Fetching API endpoint...")
        response = await page.request.get(api_url, headers={
            'Accept': '*/*',
            'Origin': 'https://www.espncricinfo.com',
            'Referer': 'https://www.espncricinfo.com/'
        })
        
        status = response.status
        print('API Status:', status)
        
        if status == 200:
            data = await response.json()
            if 'comments' in data:
                print('Success! Comments found:', len(data['comments']))
        else:
            text = await response.text()
            print('Failed response preview:', text[:200])
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

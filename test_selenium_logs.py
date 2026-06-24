"""Capture exact API requests from the browser using Selenium Performance Logs."""
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def capture_requests():
    options = Options()
    options.add_argument('--headless')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    try:
        url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(5)
        
        # Scroll to bottom multiple times
        print("Scrolling to trigger pagination...")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        print("Analyzing network logs...")
        logs = driver.get_log("performance")
        
        api_urls = []
        for entry in logs:
            log = json.loads(entry["message"])["message"]
            if log["method"] == "Network.requestWillBeSent":
                request_url = log["params"]["request"]["url"]
                if "hs-consumer-api" in request_url or "/v1/" in request_url:
                    api_urls.append(request_url)
        
        print("\nFound API requests:")
        for u in set(api_urls):
            print(u)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_requests()

from curl_cffi import requests
import re
import json

def test_ssr_scrape():
    url = "https://hs-consumer-api.cricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC"
    
    print(f"Fetching API from {url} ...")
    r = requests.get(url, impersonate="chrome")
    
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        try:
            data = r.json()
            comments = data.get("comments", [])
            print(f"SUCCESS: Fetched {len(comments)} balls from API directly!")
            if comments:
                sample = comments[0]
                print("\nSample Ball Data extracted:")
                print(f"- Over: {sample.get('oversActual')}")
                print(f"- Line: {sample.get('pitchLine')}")
                print(f"- Length: {sample.get('pitchLength')}")
        except Exception as e:
            print("Failed to parse JSON:", e)
    else:
        print("Failed. Akamai blocked the request. Response:")
        print(r.text[:200])

if __name__ == '__main__':
    test_ssr_scrape()

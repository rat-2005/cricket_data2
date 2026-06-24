from curl_cffi import requests
import json

def test_espn_api():
    url = "https://site.web.api.espn.com/apis/site/v2/sports/cricket/8676/playbyplay?event=1387599&page=1"
    
    print(f"Fetching API from {url} ...")
    r = requests.get(url, impersonate="chrome")
    
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        try:
            data = r.json()
            commentary = data.get("commentary", {})
            items = commentary.get("items", [])
            print(f"SUCCESS: Fetched {len(items)} balls from ESPN API!")
            
            if items:
                sample = items[0]
                print("\nSample Ball Data extracted:")
                # Let's print all keys in the sample ball to see if pitch data exists
                print("Available keys in ball item:", list(sample.keys()))
                
                print(f"- Over: {sample.get('over', {}).get('overs')}")
                
                # Check for pitch data
                if "pitchLine" in sample or "pitchLength" in sample:
                    print(f"- Line: {sample.get('pitchLine')}")
                    print(f"- Length: {sample.get('pitchLength')}")
                else:
                    print("⚠️ WARNING: No 'pitchLine' or 'pitchLength' found in ESPN API data!")
                    # Check nested objects for pitch data
                    print("Full item dump:", json.dumps(sample, indent=2))
                    
        except Exception as e:
            print("Failed to parse JSON:", e)
    else:
        print("Failed. Response:")
        print(r.text[:200])

if __name__ == '__main__':
    test_espn_api()

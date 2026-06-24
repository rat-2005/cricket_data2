import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

# Try competitor results for India (we need India's competitor ID)
# Let's search for India competitor ID first
url1 = f"https://api.sportradar.com/cricket-t2/en/tournaments/sr:tournament:2472/info.json?api_key={api_key}" # ICC World Cup
res1 = requests.get(url1)
if res1.status_code == 200:
    for c in res1.json().get('groups', [{}])[0].get('competitors', []):
        if c.get('name') == 'India':
            print(f"India ID: {c.get('id')}")
            
            # Now test competitor results
            url2 = f"https://api.sportradar.com/cricket-t2/en/competitors/{c.get('id')}/results.json?api_key={api_key}"
            res2 = requests.get(url2)
            print(f"Competitor Results Status: {res2.status_code}")
            if res2.status_code == 200:
                print(f"Found {len(res2.json().get('results', []))} matches!")
else:
    print(res1.status_code)

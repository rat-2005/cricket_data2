import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

url = f"https://api.sportradar.com/cricket-t2/en/schedules/2023-11-19/results.json?api_key={api_key}"
res = requests.get(url)
print(res.status_code)
if res.status_code == 200:
    data = res.json()
    for m in data.get('results', [])[:5]:
        c1 = m.get('sport_event', {}).get('competitors', [{}])[0].get('name')
        c2 = m.get('sport_event', {}).get('competitors', [{}])[-1].get('name')
        print(m.get('sport_event', {}).get('id'), c1, c2)
else:
    print(res.text[:200])

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

url1 = f"https://api.sportradar.com/cricket-t2/en/tournaments/sr:tournament:2472/schedule.json?api_key={api_key}"
res1 = requests.get(url1)
print(f"tournament schedule: {res1.status_code}")

# What if we just use the tournament schedule and skip seasons entirely?
if res1.status_code == 200:
    data = res1.json()
    print(f"Found {len(data.get('sport_events', []))} events")

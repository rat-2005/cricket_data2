import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

# Sportradar Cricket v3 endpoint for daily schedule just to test auth
# Try to get schedules for today or a known date
url = f"https://api.sportradar.com/cricket-t3/en/schedules/2024-05-26/schedule.json?api_key={api_key}"

response = requests.get(url)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("Success! Matches found:")
    for m in data.get('sport_events', [])[:5]:
        print(f"{m.get('id')} - {m.get('sport_event_context', {}).get('competition', {}).get('name')}: {m.get('competitors', [{}])[0].get('name')} vs {m.get('competitors', [{}])[-1].get('name')}")
else:
    print(response.text[:500])

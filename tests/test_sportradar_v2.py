import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

url_v2 = f"https://api.sportradar.com/cricket-t2/en/matches/sr:match:12345/timeline.json?api_key={api_key}"

response = requests.get(url_v2)
print(f"v2 Status Code: {response.status_code}")
print(response.text[:200])

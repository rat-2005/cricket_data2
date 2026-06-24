import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')

url1 = f"https://api.sportradar.com/cricket-t2/en/seasons/sr:season:41088/schedules.json?api_key={api_key}"
res1 = requests.get(url1)
print(f"schedules: {res1.status_code}")

url2 = f"https://api.sportradar.com/cricket-t2/en/seasons/sr:season:41088/schedule.json?api_key={api_key}"
res2 = requests.get(url2)
print(f"schedule: {res2.status_code}")

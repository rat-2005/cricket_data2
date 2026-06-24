import requests
import json

url = "https://assets-icc.sportz.io/cricket/v1/game/commentary?client_id=tPZJbRgIub3Vua93%2FDWtyQ%3D%3D&feed_format=json&game_id=270668&inning=1&lang=en&page_number=1&page_size=10"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
if res.status_code == 200:
    data = res.json()
    meta = data.get('meta', {})
    print(json.dumps(meta, indent=2))

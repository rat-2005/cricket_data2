import requests
import json

CLIENT_ID = "tPZJbRgIub3Vua93%2FDWtyQ%3D%3D"

for page_size in [20, 100, 500, 1000]:
    url = f"https://assets-icc.sportz.io/cricket/v1/schedule?client_id={CLIENT_ID}&feed_format=json&page_number=1&page_size={page_size}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    print(f"Testing page_size={page_size} ... Status: {res.status_code}")
    if res.status_code == 200:
        meta = res.json().get('meta', {})
        print("Meta:", meta)
    else:
        print("Text:", res.text)

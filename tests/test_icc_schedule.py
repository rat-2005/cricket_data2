import requests
import json

client_id = "tPZJbRgIub3Vua93%2FDWtyQ%3D%3D"

endpoints = [
    f"https://assets-icc.sportz.io/cricket/v1/schedule?client_id={client_id}&feed_format=json",
    f"https://assets-icc.sportz.io/cricket/v1/fixtures?client_id={client_id}&feed_format=json",
    f"https://assets-icc.sportz.io/cricket/v1/tournaments?client_id={client_id}&feed_format=json",
    f"https://assets-icc.sportz.io/cricket/v1/series?client_id={client_id}&feed_format=json"
]

headers = {"User-Agent": "Mozilla/5.0"}

try:
    res = requests.get(endpoints[0], headers=headers)
    if res.status_code == 200:
        data = res.json()
        print("Root keys:", data.keys())
        inner = data.get('data', {})
        print("Inner keys:", inner.keys())
        meta = data.get('meta', {})
        print("Meta keys:", meta)
except Exception as e:
    print("Error:", e)

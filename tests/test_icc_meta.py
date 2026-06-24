import requests
import json

client_id = "tPZJbRgIub3Vua93%2FDWtyQ%3D%3D"
game_id = "270668"

# Test a few possible metadata endpoints
endpoints = [
    f"https://assets-icc.sportz.io/cricket/v1/game/match-info?client_id={client_id}&feed_format=json&game_id={game_id}",
    f"https://assets-icc.sportz.io/cricket/v1/game/scorecard?client_id={client_id}&feed_format=json&game_id={game_id}",
    f"https://assets-icc.sportz.io/cricket/v1/game/schedule?client_id={client_id}&feed_format=json&game_id={game_id}"
]

headers = {"User-Agent": "Mozilla/5.0"}

for url in endpoints:
    res = requests.get(url, headers=headers)
    print(f"Testing {url.split('game/')[1].split('?')[0]}... Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        inner = data.get('data', {})
        if inner:
            print("Keys:", inner.keys())
            # Print a snippet of MatchInfo or similar
            if 'MatchInfo' in inner:
                print(json.dumps(inner['MatchInfo'], indent=2))
            elif 'MatchDetail' in inner:
                print(json.dumps(inner['MatchDetail'], indent=2))
        print("-" * 50)

import requests
import json

url = "https://assets-icc.sportz.io/cricket/v1/game/commentary?client_id=tPZJbRgIub3Vua93%2FDWtyQ%3D%3D&feed_format=json&game_id=270668&inning=1&lang=en&page_number=1&page_size=10"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
try:
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data_json = res.json()
        print("Data keys:", data_json.keys())
        # Print out the keys inside 'data'
        inner_data = data_json.get('data', {})
        print("Inner Data keys:", inner_data.keys() if isinstance(inner_data, dict) else type(inner_data))
        
        # Try to find commentary array
        if isinstance(inner_data, list):
            comm = inner_data
        elif isinstance(inner_data, dict):
            comm = inner_data.get('Commentary', [])
        else:
            comm = []
            
        balls = [c for c in comm if c.get('Isball') == True]
        print(f"Got {len(balls)} actual balls.")
        if balls:
            print(json.dumps(balls[0], indent=2))
    else:
        print(res.text[:500])
except Exception as e:
    print("Error:", e)

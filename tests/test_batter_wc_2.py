import requests

url = "http://127.0.0.1:5000/api/stats/batter?id=253802&league=ICC Men's T20 World Cup, 2024&format=T20&venue=All&phase=All"
res = requests.get(url)
print(res.status_code)
if res.status_code == 200:
    data = res.json()
    print("Wagon Wheel entries:", len(data.get('wagon_wheel', [])))
    print("Total Balls:", data.get('stats', {}).get('balls', 0))
else:
    print(res.text)

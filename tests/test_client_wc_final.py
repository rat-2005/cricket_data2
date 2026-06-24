from app import app

with app.test_client() as client:
    res = client.get("/api/stats/batter?id=253802&league=ICC Men's T20 World Cup, 2024&format=T20&venue=All&phase=All")
    print(res.status_code)
    data = res.get_json()
    print("Wagon Wheel:", len(data.get('wagon_wheel', [])))
    print("Total Balls:", data.get('balls', 0))
    print("Total Runs:", data.get('runs', 0))

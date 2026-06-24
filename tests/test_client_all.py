from app import app

with app.test_client() as client:
    res = client.get("/api/stats/batter?id=253802&league=All&format=All&venue=All&phase=All")
    print("Status:", res.status_code)
    data = res.get_json()
    print("Wagon Wheel:", len(data.get('wagon_wheel', [])))
    print("Total Balls:", data.get('balls', 0))
    print("Total Runs:", data.get('runs', 0))

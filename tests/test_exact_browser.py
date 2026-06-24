from app import app

# Test 1: T20I format with ICC Men's T20 World Cup league (what the user sees)
with app.test_client() as client:
    res = client.get("/api/stats/batter?id=253802&league=ICC Men's T20 World Cup&format=T20I&venue=All&phase=All")
    print("Status:", res.status_code)
    data = res.get_json()
    if data:
        print("Wagon Wheel:", len(data.get('wagon_wheel', [])))
        print("Total Balls:", data.get('balls', 0))
        print("Total Runs:", data.get('runs', 0))
        print("Shot Data:", data.get('shot_data', {}))
    else:
        print("ERROR: No JSON response!")

from app import app
import json

with app.test_client() as client:
    res = client.get("/api/stats/batter?id=253802&league=ICC Men's T20 World Cup&format=T20I&venue=All&phase=All")
    data = res.get_json()
    
    # Show first 5 wagon wheel entries to check over/ball
    for entry in data.get('wagon_wheel', [])[:10]:
        print(f"Over: {entry['over']}.{entry['ball']}  Runs: {entry['runs']}  Bowler: {entry['bowler']}  Date: {entry['date']}")

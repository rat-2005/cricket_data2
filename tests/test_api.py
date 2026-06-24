import json
from app import app

with app.app_context():
    client = app.test_client()
    response = client.get('/api/stats/batter?id=253802&league=All&phase=All&venue=All&format=All')
    data = json.loads(response.data)
    
    wagon = data.get('wagon_wheel', [])
    print(f"Total wagon elements: {len(wagon)}")
    for i, w in enumerate(wagon[:10]):
        print(f"[{i}] shot_type: {repr(w.get('shot_type'))}")

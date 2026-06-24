import json

def check_icc_json_date():
    with open('icc_json/icc_game_209291_inning_1.json', 'r') as f:
        data = json.load(f)
    
    if 'data' in data:
        print("Checking first 5 deliveries:")
        for i, deliv in enumerate(data['data']['Commentary']):
            print(f"Ball {i}: {deliv.get('Timestamp')}")
            if i >= 4:
                break

if __name__ == '__main__':
    check_icc_json_date()

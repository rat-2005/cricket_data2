import requests, json

details_url = 'http://core.espnuk.org/v2/sports/cricket/leagues/21044/events/1336043/competitions/1336043/details?page=80'
d = requests.get(details_url).json()

# get the first delivery on page 80
ref_url = d['items'][0]['$ref']
delivery = requests.get(ref_url).json()

print(json.dumps(delivery.get('innings'), indent=2))

import requests
import json
url = "http://core.espnuk.org/v2/sports/cricket/leagues/8039/events/1336043"
d = requests.get(url).json()
ro = d['competitions'][0]['competitors'][0]['roster']['$ref']
r_d = requests.get(ro).json()
a_ref = r_d['entries'][0]['athlete']['$ref']
a_data = requests.get(a_ref).json()
print(json.dumps(a_data, indent=2))

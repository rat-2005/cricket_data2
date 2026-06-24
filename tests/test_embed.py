import requests
import json
url = "http://core.espnuk.org/v2/sports/cricket/leagues/8039/events/1336043?enable=competitions,competitors,roster,details,linescores,statistics,status"
data = requests.get(url).json()

comp = data.get('competitions', [{}])[0]
details = comp.get('details', {})
linescores = comp.get('linescores', {})

print("Details type:", type(details))
if isinstance(details, dict):
    print("Details keys:", list(details.keys()))
    items = details.get('items', [])
    print("Details items count:", len(items))
    if items:
        print("First detail item keys:", list(items[0].keys()))

print("Linescores type:", type(linescores))
if isinstance(linescores, dict):
    print("Linescores keys:", list(linescores.keys()))
    items = linescores.get('items', [])
    print("Linescores items count:", len(items))
    if items:
        print("First linescore item keys:", list(items[0].keys()))

import requests
url = 'http://core.espnuk.org/v2/sports/cricket/leagues/8039/events/1336043'
data = requests.get(url).json()
comp = data['competitions'][0]
ref = comp.get('details', {}).get('$ref')
print("Details ref:", ref)
if ref:
    page = requests.get(ref).json()
    items = page.get('items', [])
    print("Page 1 items:", len(items))
    if items:
        item = items[0]
        print("First item sequence:", item.get('sequence'))
        print("First item ID:", item.get('id'))

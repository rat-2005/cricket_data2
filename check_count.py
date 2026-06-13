import urllib.request, json
total_items = 0
items_with_ref = 0
for p in range(1, 8):
    try:
        url = f'http://core.espnuk.org/v2/sports/cricket/leagues?limit=1000&page={p}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        items = data.get('items', [])
        total_items += len(items)
        items_with_ref += sum(1 for i in items if '$ref' in i)
    except Exception as e:
        print(f'Error page {p}: {e}')
print(f'Total items in arrays: {total_items}')
print(f'Items with $ref: {items_with_ref}')

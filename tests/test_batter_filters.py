import urllib.request, json
url = 'http://127.0.0.1:5000/api/batter_filters?id=253802'
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read().decode())
    leagues = d.get('leagues', [])
    for l in leagues:
        if 'Asia' in l or 'Cup' in l or 'Trophy' in l or 'Series' in l:
            print(l)

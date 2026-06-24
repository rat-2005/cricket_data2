import urllib.request, json
import re

try:
    url = 'http://127.0.0.1:5000/api/stats/batter?id=253802&year=2023&opponent=Australia'
    with urllib.request.urlopen(url) as r:
        d = json.loads(r.read().decode())
        print("Runs:", d.get("runs"))
        print("Balls:", d.get("balls"))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    html = e.read().decode()
    tb = re.search(r'(?s)Traceback \(most recent call last\):.*?<\/textarea>', html)
    if tb: print(tb.group(0).replace('</textarea>', ''))
    else: print(html[:500])

import urllib.request
import re

try:
    with urllib.request.urlopen('http://127.0.0.1:5000/api/batter_filters?id=253802') as r:
        print(r.read().decode())
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code)
    html = e.read().decode()
    # Find plaintext traceback inside Werkzeug debugger HTML
    traceback = re.search(r'(?s)Traceback \(most recent call last\):.*?<\/textarea>', html)
    if traceback:
        print(traceback.group(0).replace('</textarea>', ''))
    else:
        print('No Traceback, raw:', html[:1000])

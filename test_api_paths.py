from curl_cffi import requests
import re

r = requests.get('https://wassets.hscicdn.com/_next/static/chunks/pages/_app-9121fb96cec02d8b.js', impersonate='chrome')

print("All /v1/pages paths in _app.js:")
paths = re.findall(r'\"(/v1/pages/[^\"]+)\"', r.text)
for p in list(set(paths)):
    print(p)
    
print("\nAlso search for searchMatchOverComments implementations again:")
for m in re.finditer(r'.{0,100}searchMatchOverComments.*?\{.{0,200}\}', r.text):
    print(m.group(0))
    print("-" * 50)

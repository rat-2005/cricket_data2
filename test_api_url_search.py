from curl_cffi import requests
import re
r = requests.get('https://wassets.hscicdn.com/_next/static/chunks/pages/_app-9121fb96cec02d8b.js', impersonate='chrome')

# Find exactly how commentary pagination is fetched
print("=== Searching for commentary API path ===")
matches = re.findall(r'/v1/pages/match/commentary[^\"\']*', r.text)
for m in matches[:10]:
    print(m)

print("\n=== Searching for pagination params ===")
# Search around nextInningOver
for m in re.finditer(r'.{0,50}nextInningOver.{0,50}', r.text):
    print(m.group(0))
    
print("\n=== Searching for fromInningOver ===")
for m in re.finditer(r'.{0,50}fromInningOver.{0,50}', r.text):
    print(m.group(0))

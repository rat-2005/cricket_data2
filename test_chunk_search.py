from curl_cffi import requests
import json
import re

url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
r = requests.get(url, impersonate="chrome")
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
data = json.loads(m.group(1))

# Find the scripts loaded for this page
scripts = re.findall(r'<script src="([^"]+)"', r.text)
for script in scripts:
    if "chunks" in script:
        # Download and search
        if script.startswith("/"):
            script = "https://www.espncricinfo.com" + script
        elif not script.startswith("http"):
            continue
            
        sr = requests.get(script, impersonate="chrome")
        if "fromInningOver" in sr.text or "match/commentary" in sr.text:
            print(f"Found in: {script}")
            for match in re.findall(r'.{0,80}fromInningOver.{0,80}', sr.text):
                print(match)

from curl_cffi import requests
import json
import re

url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
r = requests.get(url, impersonate="chrome")

scripts = re.findall(r'<script src="([^"]+)"', r.text)
for script in scripts:
    if script.startswith("/"):
        script = "https://www.espncricinfo.com" + script
    elif not script.startswith("http"):
        continue
        
    sr = requests.get(script, impersonate="chrome")
    if "searchMatchOverComments" in sr.text:
        print(f"Found searchMatchOverComments in: {script}")
        for match in re.finditer(r'.{0,300}searchMatchOverComments.{0,300}', sr.text):
            print(match.group(0))
            print("-" * 50)
            
    # Search for the API endpoint path definition for match/commentary or similar
    matches = re.findall(r'/v1/pages/match/.*?[\"\']', sr.text)
    if matches:
        # print unique matches
        print(f"API paths in {script}: {list(set(matches))}")

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
            
    # Search for the API endpoint path definition for match/commentary or similar
    matches = re.findall(r'.{0,50}/v1/pages/match/commentary.{0,50}', sr.text)
    if matches:
        # print unique matches
        print(f"API paths in {script}: {list(set(matches))}")
        
    # Search for anything related to API URL building
    matches2 = re.findall(r'.{0,50}\`/v1/pages/match/\$.{0,50}', sr.text)
    if matches2:
        print(f"API builder in {script}: {list(set(matches2))}")

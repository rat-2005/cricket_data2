from curl_cffi import requests
import json
import re

url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
r = requests.get(url, impersonate="chrome")
scripts = re.findall(r'<script src="([^"]+)"', r.text)

for script in scripts:
    if "CiConsumerAPIClient" in script or "ConsumerAPI" in script or "Consumer" in script:
        if script.startswith("/"):
            script = "https://www.espncricinfo.com" + script
        print(f"Found: {script}")
        sr = requests.get(script, impersonate="chrome")
        for match in re.finditer(r'.{0,300}searchMatchOverComments.{0,300}', sr.text):
            print(match.group(0))
            print("-" * 50)
            
        # Also check for /match/commentary inside these
        for match in re.finditer(r'.{0,100}/pages/match/.{0,100}', sr.text):
            print(match.group(0))
            print("=" * 50)

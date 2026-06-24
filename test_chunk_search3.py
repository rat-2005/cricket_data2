from curl_cffi import requests
import json
import re

url = "https://www.espncricinfo.com/series/india-in-south-africa-2023-24-1387592/south-africa-vs-india-3rd-t20i-1387599/ball-by-ball-commentary"
r = requests.get(url, impersonate="chrome")

scripts = re.findall(r'<script src="([^"]+)"', r.text)
for script in scripts:
    if "chunks" in script:
        if script.startswith("/"):
            script = "https://www.espncricinfo.com" + script
        elif not script.startswith("http"):
            continue
            
        sr = requests.get(script, impersonate="chrome")
        # Let's search for "fromInningOver=" in all chunks to find the exact HTTP URL path template
        for match in re.finditer(r'.{0,100}fromInningOver.{0,100}', sr.text):
            # Check if this looks like a URL or query string builder
            if "?" in match.group(0) or "&" in match.group(0) or "+" in match.group(0) or "{" in match.group(0):
                print(f"Found in: {script}")
                print(match.group(0))
                print("-" * 50)

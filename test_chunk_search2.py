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
        if "searchMatchOverComments" in sr.text:
            print(f"Found searchMatchOverComments in: {script}")
            # print surrounding 500 characters
            for match in re.finditer(r'.{0,300}searchMatchOverComments.{0,300}', sr.text):
                print(match.group(0))
                print("-" * 50)
                
        # Also let's check for any strings containing "commentary" and "fromInningOver"
        if "fromInningOver" in sr.text and "/v1/pages/" in sr.text:
            for match in re.finditer(r'.{0,150}/v1/pages/.{0,150}', sr.text):
                if "fromInningOver" in match.group(0):
                    print(f"Found API path in: {script}")
                    print(match.group(0))
                    print("-" * 50)

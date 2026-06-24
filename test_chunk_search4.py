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
    
    # We want to find the implementation of searchMatchOverComments
    if "searchMatchOverComments" in sr.text:
        # Check if it defines a method
        if re.search(r'searchMatchOverComments\s*\(', sr.text) or re.search(r'searchMatchOverComments\s*=', sr.text) or re.search(r'searchMatchOverComments:', sr.text):
            print(f"Implementation might be in: {script}")
            for m in re.finditer(r'.{0,300}searchMatchOverComments.{0,300}', sr.text):
                print(m.group(0))
                print("-" * 50)

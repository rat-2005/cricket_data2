import urllib.request
import json
import time

def fetch(url):
    print(f"Fetching {url}")
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Runs: {data['runs']}")
    except Exception as e:
        print(f"Error: {e}")

fetch("http://127.0.0.1:5000/api/stats/batter?id=49752&format=ODI")
fetch("http://127.0.0.1:5000/api/stats/batter?id=49752&format=T20I")
fetch("http://127.0.0.1:5000/api/stats/batter?id=49752&format=ODI,T20I")
fetch("http://127.0.0.1:5000/api/stats/batter?id=49752&format=ODI&format=T20I")

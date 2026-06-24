import urllib.request
import json

def test_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req)
        print(f"[OK 200] {url}")
        return True
    except Exception as e:
        print(f"[{e}] {url}")
        return False

urls = [
    "https://sports.core.api.espn.com/v2/sports/cricket/leagues",
    "https://sports.core.api.espn.com/v3/sports/cricket/leagues",
    "https://sports.core.api.espn.com/v2/sports/cricket/leagues/1510719",
    "https://sports.core.api.espn.com/v3/sports/cricket/leagues/1510719",
    "https://sports.core.api.espn.com/v2/sports/cricket/events/1426261",
    "https://sports.core.api.espn.com/v3/sports/cricket/events/1426261"
]

for u in urls:
    test_url(u)

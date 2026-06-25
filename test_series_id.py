import time
import hmac
import hashlib
from curl_cffi import requests

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
BASE_URL = "https://hs-consumer-api.cricinfo.com"

def get_auth_token(path):
    t = f"exp={int(time.time()) + 60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

path = f"/v1/pages/match/commentary?lang=en&seriesId=999999&matchId=1535009&sortDirection=DESC"
headers = {
    "x-hsci-auth-token": get_auth_token(path),
    "Origin": "https://www.espncricinfo.com",
    "Referer": "https://www.espncricinfo.com/",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(f"{BASE_URL}{path}", headers=headers, impersonate="chrome")
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Match Title:", data.get('match', {}).get('title'))
else:
    print("Failed")

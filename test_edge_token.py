"""
Generate the X-Hsci-Auth-Token using the extracted encryption key.
The token is generated using Akamai EdgeAuth (HMAC-SHA256 based URL tokens).
"""
from curl_cffi import requests
import hmac
import hashlib
import time
import json

# Extracted from the _app JS bundle
ENCRYPTION_KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
TOKEN_VALIDITY = 60  # seconds

def generate_edge_token(path):
    """Generate Akamai EdgeAuth token for the given URL path.
    
    This replicates the akamai-edgeauth npm package's generateURLToken() method.
    The token format is: exp=<expiry>&acl=<path>&hmac=<hmac>
    """
    start_time = int(time.time())
    end_time = start_time + TOKEN_VALIDITY
    
    # URL-encode the path for the ACL (Access Control List)
    # escapeEarly is true, so we encode before HMAC
    acl = path
    
    # Build the token fields (this is how akamai-edgeauth constructs it)
    # The format varies, let's try the most common patterns
    
    # Pattern 1: Simple exp + acl + hmac
    new_token = f"exp={end_time}~acl={acl}"
    key_bytes = bytes.fromhex(ENCRYPTION_KEY)
    digest = hmac.new(key_bytes, new_token.encode('utf-8'), hashlib.sha256).hexdigest()
    token = f"{new_token}~hmac={digest}"
    
    return token

# Test it
api_path = "/v1/pages/match/commentary?lang=en&seriesId=1387592&matchId=1387599&sortDirection=DESC"
token = generate_edge_token(api_path)
print(f"Generated token: {token}")

# Now try hitting the API with this token
session = requests.Session(impersonate="chrome")

api_url = f"https://hs-consumer-api.cricinfo.com{api_path}"
headers = {
    "x-hsci-auth-token": token,
    "Origin": "https://www.espncricinfo.com",
    "Referer": "https://www.espncricinfo.com/",
    "Accept": "application/json",
}

print(f"\nHitting API: {api_url}")
r = session.get(api_url, headers=headers)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    comments = data.get("comments", [])
    print(f"SUCCESS! Got {len(comments)} comments!")
    if comments:
        sample = comments[0]
        print(f"  pitchLine: {sample.get('pitchLine')}")
        print(f"  pitchLength: {sample.get('pitchLength')}")
        print(f"  shotType: {sample.get('shotType')}")
elif r.status_code == 403:
    print("Still blocked. Let's try different token formats...")
    
    # Pattern 2: st (start time) + exp + acl
    for pattern_name, token_str in [
        ("st+exp+acl", f"st={int(time.time())}~exp={int(time.time())+60}~acl={api_path}"),
        ("exp+acl (url encoded)", f"exp={int(time.time())+60}~acl={api_path.replace('&', '%26')}"),
        ("exp+url (not acl)", f"exp={int(time.time())+60}~url={api_path}"),
    ]:
        key_bytes = bytes.fromhex(ENCRYPTION_KEY)
        digest = hmac.new(key_bytes, token_str.encode('utf-8'), hashlib.sha256).hexdigest()
        token2 = f"{token_str}~hmac={digest}"
        headers["x-hsci-auth-token"] = token2
        r2 = session.get(api_url, headers=headers)
        print(f"  {pattern_name}: {r2.status_code}")
        if r2.status_code == 200:
            data = r2.json()
            print(f"  SUCCESS! Comments: {len(data.get('comments', []))}")
            break
else:
    print(f"Unexpected status: {r.text[:300]}")

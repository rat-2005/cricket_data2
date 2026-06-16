import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://sports.core.api.espn.com/v2/sports/cricket/teams/335970', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read())
        print(f"Success! Data: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"Error: {e}")

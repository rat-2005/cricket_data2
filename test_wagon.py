import urllib.request, urllib.parse, json

sql = "SELECT wagonX, wagonY, wagonZone, batsmanRuns, shotType FROM cricinfo_parquet cp JOIN cricinfo_metadata m ON cp.match_id = m.match_id WHERE batsmanPlayerId = 49752 AND bowlerPlayerId = 103878"
url = "http://127.0.0.1:5000/api/debug?sql=" + urllib.parse.quote(sql)
try:
    res = json.loads(urllib.request.urlopen(url).read().decode())
    print("All Shots vs Haris Rauf:")
    for r in res:
        print(r)
except Exception as e:
    print("Error:", e)

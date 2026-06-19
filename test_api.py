import urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:5000/api/faceoff_filters?batter_id=253802&bowler_id=26421')
except Exception as e:
    print(e.read().decode())

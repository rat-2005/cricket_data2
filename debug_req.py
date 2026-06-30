
import requests

url = "http://127.0.0.1:5000/api/stats/batter?id=253802&format=ODI,T20I"
r = requests.get(url)
data = r.json()
print("Runs:", data.get('runs'))
print("Matches:", data.get('matches'))

# Let's also test ODI only and T20I only
url2 = "http://127.0.0.1:5000/api/stats/batter?id=253802&format=ODI"
print("ODI Runs:", requests.get(url2).json().get('runs'))

url3 = "http://127.0.0.1:5000/api/stats/batter?id=253802&format=T20I"
print("T20I Runs:", requests.get(url3).json().get('runs'))

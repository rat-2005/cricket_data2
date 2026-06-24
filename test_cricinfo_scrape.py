import requests

url = 'https://hs-consumer-api.cricinfo.com/v1/pages/match/commentary?lang=en&seriesId=1527147&matchId=1527152&sortDirection=DESC'
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.espncricinfo.com',
    'Referer': 'https://www.espncricinfo.com/',
    'Sec-Ch-Ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
}

# Test without token
res = requests.get(url, headers=headers)
print('Status without token:', res.status_code)

# Test with token from screenshot
headers['X-Hsci-Auth-Token'] = 'exp=1782226225~hmac=c57cfa871f57feff5005fde25f93e71a8eafbef25adb8334ac803a181f79dfc9'
res = requests.get(url, headers=headers)
print('Status with token:', res.status_code)

if res.status_code == 200:
    try:
        data = res.json()
        print('Keys:', data.keys())
        if 'comments' in data:
            print('Number of comments:', len(data['comments']))
    except Exception as e:
        print('Error parsing JSON:', e)
else:
    print('Response:', res.text[:200])

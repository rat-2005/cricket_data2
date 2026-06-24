with open('app.py', 'r') as f:
    content = f.read().split('\n')
start = 0
for i, line in enumerate(content):
    if 'def stats_batter():' in line:
        start = i
        break

for i in range(start, start + 300):
    if "if league_filter == 'Series':" in content[i]:
        print('\n'.join(content[i-5:i+20]))
        break

with open('app.py', 'r') as f:
    content = f.read().split('\n')
start = 0
for i, line in enumerate(content):
    if 'def batter_filters():' in line:
        start = i
    if start > 0 and 'where_clause_d' in line:
        print('\n'.join(content[start:i+5]))
        break

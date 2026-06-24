import re
with open('app.py', 'r') as f:
    content = f.read()

# Fix spacing: if league_filter != 'All': followed by if league_filter == 'Series':
content = re.sub(r"if league_filter != 'All':\s+if league_filter == 'Series':", "if league_filter != 'All':\n        if league_filter == 'Series':", content)
content = re.sub(r"if league_filter != 'All':\s+if league_filter == 'Asia Cup':", "if league_filter != 'All':\n        if league_filter == 'Asia Cup':", content)

with open('app.py', 'w') as f:
    f.write(content)

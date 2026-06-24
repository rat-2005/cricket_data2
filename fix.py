import re
with open('app.py', 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "if league_filter != 'All':" in line and "if league_filter == 'Series':" in line:
        lines[i] = line.replace("if league_filter != 'All':        if league_filter == 'Series':", "if league_filter != 'All':\n        if league_filter == 'Series':")
        lines[i] = lines[i].replace("if league_filter != 'All':                if league_filter == 'Series':", "if league_filter != 'All':\n        if league_filter == 'Series':")
with open('app.py', 'w') as f:
    f.writelines(lines)
